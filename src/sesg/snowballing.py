from itertools import islice
from multiprocessing import Pool
from typing import Iterable, Iterator, List, Tuple, TypedDict, TypeVar

from thefuzz import process


T = TypeVar("T")


def _window(
    seq: Iterable[T],
    size: int,
) -> Iterator[Tuple[T, ...]]:
    """Creates an iterator over overlapping subslices of the given size.

    Args:
        seq (Iterable[T]): Sequence to iterate over.
        size (int): Size of each subslice.

    Yields:
        A subslice with the given size.

    Examples:
        >>> elements = [1, 2, 3, 4, 5, 6]
        >>> for subslice in _window(elements, 3):
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


def _study_cites_title(
    title: str,
    study: str,
) -> bool:
    """Uses `thefuzz.process.extractOne` to determine if a study cites a title.

    Args:
        title (str): Title to search for.
        study (str): Text of the study.

    Returns:
        True if the study cites the title, False otherwise.

    Examples:
        >>> _study_cites_title(
        ...     title="regression tests for machine learning models: a systematic literature review",
        ...     study="long text here very long REFERENCES: regression tests for machine learning models: a systematic literature review",
        ... )
        True
    """  # noqa: E501
    window_size = len(title)
    options = ["".join(x) for x in _window(study, window_size)]

    result = process.extractOne(title, options)

    if result is not None and result[1] >= 90:
        return True

    return False


class _PooledStudyCitesTitleArgs(TypedDict):
    """Data container for the `_pooled_study_cites_title` function, with the goal of improving type safety.

    Args:
        title (str): Title to search for
        study (str): Text of the study.
        skip (bool): Indicates if should skip the execution and return False.
    """  # noqa: E501

    title: str
    study: str
    skip: bool


def _pooled_study_cites_title(
    args: _PooledStudyCitesTitleArgs,
) -> bool:
    """Replicates `_study_cites_title` behaviour, with slight modifications to work
    well with `multiprocessing.Pool`.

    Args:
        args (_PooledStudyCitesTitleArgs): args of this function.

    Returns:
        False if skip is True, the result of `_study_cites_title(args["title"], args["study"])` otherwise.

    Examples:
        >>> _pooled_study_cites_title(
        ...     _PooledStudyCitesTitleArgs(
        ...         title="regression tests for machine learning models: a systematic literature review",
        ...         study="TITLE: regression tests for machine learning models: a systematic literature review. Abstract: abstract here",
        ...         skip=True,
        ...     )
        ... )
        False
    """  # noqa: E501
    if args["skip"]:
        return False

    return _study_cites_title(args["title"], args["study"])


def _preprocess_title(
    title: str,
) -> str:
    """Processes the title in the following order:
    1. Removes leading and trailing whitespaces
    1. Turns to lower case
    1. Removes spaces and dots

    Args:
        title (str): Title to preprocess.

    Returns:
        Preprocessed title.

    Examples:
        >>> _preprocess_title(title=" title. HERE ")
        'titlehere'
    """
    return title.strip().lower().replace(" ", "").replace(".", "")


def _preprocess_study(
    study_text: str,
) -> str:
    r"""Processes the study in the following manner:
    1. Removes leading and trailing whitespaces
    1. Turns to lower case
    1. Removes line breaks, line carriages, spaces, and dots

    Args:
        study_text (str): Study's text to preprocess

    Returns:
        Preprocessed study.

    Examples:
        >>> _preprocess_study(study_text=" text. \n \r\n HERE ")
        'texthere'
    """
    return (
        study_text.strip()
        .lower()
        .replace("\n", "")
        .replace("\r", "")
        .replace(" ", "")
        .replace(".", "")
    )


class SnowballingStudy:
    r"""Represents a study that will be included in backward snowballing.
    The constructor will preprocess the title and text content to the correct
    format.

    Args:
        id (int): Identifier of the study. Could be a database id, for example.
        title (str): Title of the study.
        text_content (str): Content of the study. Could be extracted from a PDF with CERMINE.

    Examples:
        >>> s = SnowballingStudy(id=1, title=" title. HERE ", text_content=" text. \n \r\n HERE ")
        >>> s.title == "titlehere", s.text_content == "texthere"
        (True, True)
    """  # noqa: E501

    id: int
    title: str
    text_content: str

    def __init__(
        self,
        id: int,
        title: str,
        text_content: str,
    ) -> None:
        self.id = id
        self.title = _preprocess_title(title)
        self.text_content = _preprocess_study(text_content)


def backwards_snowballing(
    studies: List[SnowballingStudy],
) -> Iterator[Tuple[SnowballingStudy, List[SnowballingStudy]]]:
    """Runs backwads snowballing in the given list of studies.
    The graph returned is in the form of an Adjacency List

    Args:
        studies (List[SnowballingStudy]): List of studies with id, title, and text content.

    Yields:
        Iterator of tuples, where the tuple holds a study, and the studies that are referenced.

    Examples:
        >>> studies: List[SnowballingStudy] = [
        ...     SnowballingStudy(id=1, title="title 1", text_content="... REFERENCES: machine learning, a SLR"),
        ...     SnowballingStudy(id=2, title="machine learning, a SLR", text_content="... REFERENCES: other studies"),
        ... ]
        >>>
        >>> for study, references in backwards_snowballing(studies):
        ...     print((study.id, [r.id for r in references]))
        (1, [2])
        (2, [])
    """  # noqa: E501

    for study_index, study in enumerate(studies):
        with Pool() as p:
            # if `result[j]` is True then the current study cites title `j`
            result: List[bool] = p.map(
                _pooled_study_cites_title,
                [
                    {
                        # when `i == j`, we are checking if study `i` cites itself,
                        # so we skip and set it as False
                        "skip": study_index == reference_index,
                        "study": study.text_content,
                        "title": reference.title,
                    }
                    for reference_index, reference in enumerate(studies)
                ],
            )

        references: List[SnowballingStudy] = list()

        for result_index, is_cited in enumerate(result):
            if is_cited:
                referenced_study = studies[result_index]
                references.append(referenced_study)

        yield study, references
