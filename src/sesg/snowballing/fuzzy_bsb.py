"""Fuzzy backward snowballing module.

Performs backward snowballing using fuzzy matching with 
[`rapidfuzz`](https://github.com/maxbachmann/RapidFuzz)
to perform string similarity checks.
"""  # noqa: E501

from itertools import islice
from multiprocessing import Pool
from typing import Iterable, Iterator, TypedDict, TypeVar

from rapidfuzz import process


T = TypeVar("T")


def window(
    seq: Iterable[T],
    *,
    size: int,
) -> Iterator[tuple[T, ...]]:
    """Creates an iterator over overlapping subslices of the given size.

    Args:
        seq (Iterable[T]): Sequence to iterate over.
        size (int): Size of each subslice.

    Yields:
        A subslice with the given size.

    Examples:
        >>> elements = [1, 2, 3, 4, 5, 6]
        >>> for subslice in window(elements, size=3):
        ...     print(subslice)
        (1, 2, 3)
        (2, 3, 4)
        (3, 4, 5)
        (4, 5, 6)
    """
    it = iter(seq)
    result = tuple(islice(it, size))

    if len(result) == size:
        yield result

    for elem in it:
        result = result[1:] + (elem,)
        yield result


def check_title_is_in_text(
    *,
    title: str,
    text: str,
) -> bool:
    """Uses `thefuzz.process.extractOne` to determine if a title is in a piece of text.

    Args:
        title (str): Title to search for.
        text (str): Text of the study.

    Returns:
        True if the title is in the text, False otherwise.

    Examples:
        >>> check_title_is_in_text(
        ...     text="long text here very long REFERENCES: regression tests for machine learning models: a systematic literature review",
        ...     title="regression tests for machine learning models: a systematic literature review",
        ... )
        True
    """  # noqa: E501
    window_size = len(title)
    options = ["".join(x) for x in window(text, size=window_size)]

    result = process.extractOne(title, options)

    if result is not None and result[1] >= 90:
        return True

    return False


class PooledTitleIsInTextArgs(TypedDict):
    """Data container for the arguments of the [`pooled_study_cites_title`][sesg.snowballing.fuzzy_bsb.pooled_check_title_is_in_text] function.

    Attributes:
        title (str): Title to search for
        text (str): Text of the study.
        skip (bool): Indicates if should skip the execution and return False.
    """  # noqa: E501

    title: str
    text: str
    skip: bool


def pooled_check_title_is_in_text(
    args: PooledTitleIsInTextArgs,
) -> bool:
    """Replicates [`check_title_is_in_text`][sesg.snowballing.fuzzy_bsb.check_title_is_in_text] behaviour, with slight modifications to work well with `multiprocessing.Pool`.

    Args:
        args (PooledTitleIsInTextArgs): args of this function.

    Returns:
        False if skip is True, the result of `check_title_is_in_text(args["title"], args["study"])` otherwise.

    Examples:
        >>> pooled_check_title_is_in_text(
        ...     {
        ...         "title": "regression tests for machine learning models: a systematic literature review",
        ...         "text": "TITLE: regression tests for machine learning models: a systematic literature review. Abstract: abstract here",
        ...         "skip": True,
        ...     }
        ... )
        False
    """  # noqa: E501
    if args["skip"]:
        return False

    return check_title_is_in_text(text=args["text"], title=args["title"])


def preprocess_title(
    title: str,
) -> str:
    """Processes the title in the following manner.

    1. Removes leading and trailing whitespaces
    1. Turns to lower case
    1. Removes spaces and dots

    Args:
        title (str): Title to preprocess.

    Returns:
        Preprocessed title.

    Examples:
        >>> preprocess_title(" title. HERE ")
        'titlehere'
    """
    return title.strip().lower().replace(" ", "").replace(".", "")


def preprocess_text(
    text: str,
) -> str:
    r"""Processes the study in the following manner.

    1. Removes leading and trailing whitespaces
    1. Turns to lower case
    1. Removes line breaks, line carriages, spaces, and dots

    Args:
        text (str): Study's text to preprocess

    Returns:
        Preprocessed text.

    Examples:
        >>> preprocess_text(" text. \n \r\n HERE ")
        'texthere'
    """
    return (
        text.strip()
        .lower()
        .replace("\n", "")
        .replace("\r", "")
        .replace(" ", "")
        .replace(".", "")
    )


class FuzzyBackwardSnowballingStudy:
    r"""Represents a study that will be included in backward snowballing.

    The constructor will preprocess the title and text content to the correct format.

    Examples:
        >>> s = FuzzyBackwardSnowballingStudy(id=1, title=" title. HERE ", text_content=" text. \n \r\n HERE ")
        >>> s.title == "titlehere", s.text_content == "texthere"
        (True, True)
    """  # noqa: E501

    __id: int
    __title: str
    __text_content: str

    def __init__(
        self,
        *,
        id: int,
        title: str,
        text_content: str,
    ) -> None:
        """Creates an instance of a SnowballingStudy.

        Args:
            id (int): Identifier of the study. Could be a database id, for example.
            title (str): Title of the study.
            text_content (str): Content of the study. Could be extracted from a PDF with CERMINE.
        """  # noqa: E501
        self.__id = id
        self.__title = preprocess_title(title)
        self.__text_content = preprocess_text(text_content)

    @property
    def id(self) -> int:
        """ID of the study."""
        return self.__id

    @property
    def title(self) -> str:
        """Title of the study."""
        return self.__title

    @property
    def text_content(self) -> str:
        """Text content of the study."""
        return self.__text_content


def fuzzy_backward_snowballing(
    studies: list[FuzzyBackwardSnowballingStudy],
) -> Iterator[
    tuple[FuzzyBackwardSnowballingStudy, list[FuzzyBackwardSnowballingStudy]]
]:
    """Runs backward snowballing in the given list of studies.

    Args:
        studies (list[SnowballingStudy]): List of studies with id, title, and text content.

    Yields:
        A tuple holding a study, and it's references.

    Examples:
        >>> studies: list[FuzzyBackwardSnowballingStudy] = [
        ...     FuzzyBackwardSnowballingStudy(id=1, title="title 1", text_content="... REFERENCES: machine learning, a SLR"),
        ...     FuzzyBackwardSnowballingStudy(id=2, title="machine learning, a SLR", text_content="... REFERENCES: other studies"),
        ... ]
        >>>
        >>> for study, references in fuzzy_backward_snowballing(studies):
        ...     print((study.id, [r.id for r in references]))
        (1, [2])
        (2, [])
    """  # noqa: E501
    for study_index, study in enumerate(studies):
        with Pool() as p:
            func_args: list[PooledTitleIsInTextArgs] = [
                {
                    # when `study_index == reference_index`, we are checking if study a cites itself,  # noqa: E501
                    # so we skip and set it as False
                    "skip": study_index == reference_index,
                    "text": study.text_content,
                    "title": reference.title,
                }
                for reference_index, reference in enumerate(studies)
            ]

            # if `is_cited_list[j]` is True then the current study cites title `j`
            is_cited_list: list[bool] = p.map(
                pooled_check_title_is_in_text,
                func_args,
            )

        references = [ref for ref, is_cited in zip(studies, is_cited_list) if is_cited]

        yield study, references
