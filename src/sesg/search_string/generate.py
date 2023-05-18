"""Search string generation module.

This module provides an interface to generate a search string based on a list of topics,
allowing variations on the number of words per topic to use, and number of similar words to generate for each word of each topic.
"""  # noqa: E501

from typing import Iterable, Literal, TypedDict

from .similar_words import (
    SimilarWordsFinder,
)


def _join_tokens_with_operator(
    operator: Literal["AND", "OR"],
    tokens_list: Iterable[str],
    *,
    use_double_quotes: bool = False,
    use_parenthesis: bool = False,
) -> str:
    """Joins the tokens in the list using the provided operator.

    First checks if should surround with double quotes, then checks if should surround with parenthesis.
    If both are set to True, will add both double quotes and parenthesis.

    Args:
        operator (Literal["AND", "OR"]): Operator to use to join.
        tokens_list (Iterable[str]): Tokens to join.
        use_double_quotes (Optional[bool]): Whether to put double quotes surrounding each token.
        use_parenthesis (Optional[bool]): Whether to put parenthesis surrounding each token.

    Returns:
        A string with the joined tokens.

    Examples:
        >>> _join_tokens_with_operator("AND", ["machine", "learning", "SLR"], use_double_quotes=True)
        '"machine" AND "learning" AND "SLR"'
    """  # noqa: E501
    if use_double_quotes:
        tokens_list = (f'"{token}"' for token in tokens_list)

    if use_parenthesis:
        tokens_list = (f"({token})" for token in tokens_list)

    return f" {operator} ".join(tokens_list)


def _join_topics_without_similar_words(
    topics_list: list[list[str]],
) -> str:
    """Joins the topics in the list, creating a search string.

    Specialization of [sesg.search_string._join_tokens_with_operator][] to join a list of
    topics that does not have similar words included.

    Each topic is a list of words (or tokens).

    Args:
        topics_list (list[list[str]]): List of topics to join.

    Returns:
        A valid search string.

    Examples:
        >>> _join_topics_without_similar_words([["machine", "learning"], ["code", "smell"]])
        '("machine" AND "learning") OR ("code" AND "smell")'
    """  # noqa: E501
    topics_part: list[str] = list()
    for topic_words_list in topics_list:
        s = _join_tokens_with_operator("AND", topic_words_list, use_double_quotes=True)
        topics_part.append(s)

    string = _join_tokens_with_operator("OR", topics_part, use_parenthesis=True)

    return string


def _join_topics_with_similar_words(
    topics_list: list[list[list[str]]],
) -> str:
    """Joins the topics in the list, creating a search string.

    Specialization of [sesg.search_string._join_tokens_with_operator][] to join a list of
    topics that includes similar words.

    Each topic is a list of words that are considered similar.

    Args:
        topics_list (list[list[list[str]]]): List of topics to join.

    Returns:
        A valid search string.

    Examples:
        >>> _join_topics_with_similar_words([
        ...     [["machine", "computer"], ["learning", "knowledge"]],
        ...     [["code", "software"], ["smell", "defect"]]
        ... ])
        '(("machine" OR "computer") AND ("learning" OR "knowledge")) OR (("code" OR "software") AND ("smell" OR "defect"))'
    """  # noqa: E501
    topics_part: list[str] = list()
    for topic in topics_list:
        similar_words_part: list[str] = list()
        for similar_words in topic:
            s = _join_tokens_with_operator("OR", similar_words, use_double_quotes=True)
            similar_words_part.append(s)

        s = _join_tokens_with_operator("AND", similar_words_part, use_parenthesis=True)
        topics_part.append(s)

    string = _join_tokens_with_operator("OR", topics_part, use_parenthesis=True)

    return string


class EnrichmentStudy(TypedDict):
    """Data container for a study that will be used to generate an enrichment text.

    Attributes:
        title (str): Title of the study.
        abstract (str): Abstract of the study.

    Examples:
        >>> study: EnrichmentStudy = {
        ...     "title": "machine learning",
        ...     "abstract": "machine learning is often used in the industry with the goal of...",
        ... }
        >>> study
        {'title': 'machine learning', 'abstract': 'machine learning is often used in the industry with the goal of...'}
    """  # noqa: E501

    title: str
    abstract: str


def create_enrichment_text(
    studies_list: list[EnrichmentStudy],
) -> str:
    r"""Creates a piece of text that consists of the concatenation of the title and abstract of each study.

    Can be used with the [`sesg.search_string.generate_search_string`][] function.

    Args:
        studies_list (list[EnrichmentStudy]): List of studies with title and abstract.

    Returns:
        The enrichment text.

    Examples:
        >>> studies = [
        ...     EnrichmentStudy(title="title1", abstract="abstract1"),
        ...     EnrichmentStudy(title="title2", abstract="abstract2 \r\ntext"),
        ...     EnrichmentStudy(title="title3", abstract="abstract3"),
        ... ]
        >>> create_enrichment_text(studies_list=studies)
        'title1 abstract1\ntitle2 abstract2 #.text\ntitle3 abstract3\n'
    """  # noqa: E501
    enrichment_text = ""
    for study in studies_list:
        title = study["title"]
        abstract = study["abstract"]

        line = f"{title} {abstract}".strip().replace("\r\n", "#.") + "\n"
        enrichment_text += line

    return enrichment_text


def _reduce_number_of_words_per_topic(
    topics_list: list[list[str]],
    n_words_per_topic: int,
) -> list[list[str]]:
    """Reduces the number of words in each topic.

    Args:
        topics_list (list[list[str]]): List with the topics.
        n_words_per_topic (int): Number of words to keep in each topic.

    Returns:
        List with the reduced topics.

    Examples:
        >>> _reduce_number_of_words_per_topic([["machine", "learning"], ["code", "smell"]], 1)
        [['machine'], ['code']]
    """  # noqa: E501
    topics_list = [topic[:n_words_per_topic] for topic in topics_list]

    return topics_list


def _generate_search_string_without_similar_words(
    *,
    topics_list: list[list[str]],
    n_words_per_topic: int,
) -> str:
    """Generates a search string by reducing the number of topics, and joining the reduced topics.

    Args:
        topics_list (list[list[str]]): List of topics to use.
        n_words_per_topic (int): Number of words to keep in each topic.

    Returns:
        The search string.
    """  # noqa: E501
    topics_list = _reduce_number_of_words_per_topic(
        topics_list=topics_list,
        n_words_per_topic=n_words_per_topic,
    )

    string = _join_topics_without_similar_words(topics_list)

    return string


def _generate_search_string_with_similar_words(
    *,
    topics_list: list[list[str]],
    n_words_per_topic: int,
    n_similar_words_per_word: int,
    similar_words_finder: SimilarWordsFinder,
) -> str:
    """Generates a search string with the following steps.

    1. Reduces the number of words per topic.
    1. For each word in each topic, finds similar words with BERT.
    1. Filters out similar words that have a high string equality (meaning a low Levenshtein Distance).

    Args:
        topics_list (list[list[str]]): List of topics to use.
        n_words_per_topic (int): Number of words to keep in each topic.
        n_similar_words_per_word (int): Number of similar words to generate for each word in each topic.
        similar_words_finder (SimilarWordsFinder): Instance of SimilarWordsFinder.

    Returns:
        The search string.
    """  # noqa: E501
    topics_list = _reduce_number_of_words_per_topic(
        topics_list=topics_list,
        n_words_per_topic=n_words_per_topic,
    )

    topics_with_similar_words: list[list[list[str]]] = list()
    for topic in topics_list:
        topic_part: list[list[str]] = list()
        for token in topic:
            similar_words = similar_words_finder(token)

            # limiting the number of similar words
            # we add one because the word itself is included in the similar_words list
            topic_part.append(similar_words[: n_similar_words_per_word + 1])

        topics_with_similar_words.append(topic_part)

    string = _join_topics_with_similar_words(topics_with_similar_words)

    return string


def generate_search_string(
    *,
    topics_list: list[list[str]],
    n_words_per_topic: int,
    n_similar_words_per_word: int,
    similar_words_finder: SimilarWordsFinder,
) -> str:
    """Generates a search string that will be enriched with the desired number of similar words.

    Args:
        topics_list (list[list[str]]): List of topics to use.
        n_words_per_topic (int): Number of words to keep in each topic.
        n_similar_words_per_word (int): Number of similar words to generate for each word in each topic.
        similar_words_finder (SimilarWordsFinder): Instance of SimilarWordsFinder.

    Returns:
        A search string.
    """  # noqa: E501
    if n_similar_words_per_word == 0:
        return _generate_search_string_without_similar_words(
            topics_list=topics_list,
            n_words_per_topic=n_words_per_topic,
        )

    return _generate_search_string_with_similar_words(
        topics_list=topics_list,
        n_words_per_topic=n_words_per_topic,
        n_similar_words_per_word=n_similar_words_per_word,
        similar_words_finder=similar_words_finder,
    )
