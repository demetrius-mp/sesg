"""Search string formulation utilities."""

from typing import Iterable, Literal


class InvalidPubyearBoundariesError(ValueError):
    """The provided pubyear boundaries are invalid."""


def set_pub_year_boundaries(
    string: str,
    *,
    min_year: int | None = None,
    max_year: int | None = None,
) -> str:
    """Given a search string, will append `PUBYEAR >` and `PUBYEAR <` boundaries as needed.

    Args:
        string (str): A search string.
        min_year (int | None, optional): Minimum year of publication. Defaults to None.
        max_year (int | None, optional): Maximum year of publication. Defaults to None.

    Returns:
        A search string with PUBYEAR boundaries.

    Examples:
        >>> set_pub_year_boundaries(string='title("machine" and "learning")', max_year=2018)
        'title("machine" and "learning") AND PUBYEAR < 2018'
    """  # noqa: E501
    if min_year is not None and max_year is not None and min_year >= max_year:
        raise InvalidPubyearBoundariesError("Max year must be greater than min year")

    if min_year is not None:
        string += f" AND PUBYEAR > {min_year}"

    if max_year is not None:
        string += f" AND PUBYEAR < {max_year}"

    return string


def join_tokens_with_operator(
    tokens: Iterable[str],
    operator: Literal["AND", "OR"],
    *,
    use_double_quotes: bool = False,
    use_parenthesis: bool = False,
) -> str:
    """Joins the tokens in the list using the provided operator.

    First checks if should surround with double quotes, then checks if should surround with parenthesis.
    If both are set to True, will add both double quotes and parenthesis.

    Args:
        operator (Literal["AND", "OR"]): Operator to use to join.
        tokens (Iterable[str]): Tokens to join.
        use_double_quotes (Optional[bool]): Whether to put double quotes surrounding each token.
        use_parenthesis (Optional[bool]): Whether to put parenthesis surrounding each token.

    Returns:
        A string with the joined tokens.

    Examples:
        >>> join_tokens_with_operator(["machine", "learning", "SLR"], "AND", use_double_quotes=True)
        '"machine" AND "learning" AND "SLR"'
    """  # noqa: E501
    if use_double_quotes:
        tokens = (f'"{token}"' for token in tokens)

    if use_parenthesis:
        tokens = (f"({token})" for token in tokens)

    return f" {operator} ".join(tokens)


def join_topics_without_similar_words(
    topics: list[list[str]],
) -> str:
    """Joins the topics in the list, creating a search string.

    Specialization of [sesg.search_string.formulation.join_tokens_with_operator][] to join a list of
    topics that does not have similar words included.

    Each topic is a list of words (or tokens).

    Args:
        topics (list[list[str]]): List of topics to join.

    Returns:
        A valid search string.

    Examples:
        >>> join_topics_without_similar_words([["machine", "learning"], ["code", "smell"]])
        '("machine" AND "learning") OR ("code" AND "smell")'
    """  # noqa: E501
    topics_part: list[str] = []
    for topic_words in topics:
        # words from the same topic are joined with AND
        s = join_tokens_with_operator(topic_words, "AND", use_double_quotes=True)
        topics_part.append(s)

    # topics are joined with OR
    string = join_tokens_with_operator(topics_part, "OR", use_parenthesis=True)

    return string


def join_topics_with_similar_words(
    topics: list[list[list[str]]],
) -> str:
    """Joins the topics in the list, creating a search string.

    Specialization of [sesg.search_string.formulation.join_tokens_with_operator][] to join a list of
    topics that includes similar words.

    Each topic is a list of words that are considered similar.

    Args:
        topics (list[list[list[str]]]): List of topics to join.

    Returns:
        A valid search string.

    Examples:
        >>> join_topics_with_similar_words([
        ...     [["machine", "computer"], ["learning", "knowledge"]],
        ...     [["code", "software"], ["smell", "defect"]]
        ... ])
        '(("machine" OR "computer") AND ("learning" OR "knowledge")) OR (("code" OR "software") AND ("smell" OR "defect"))'
    """  # noqa: E501
    topics_part: list[str] = []
    for topic in topics:
        similar_words_part: list[str] = []
        for similar_words in topic:
            # similar words are joined with OR
            s = join_tokens_with_operator(similar_words, "OR", use_double_quotes=True)
            similar_words_part.append(s)

        # sets of similar words are joined with AND
        s = join_tokens_with_operator(similar_words_part, "AND", use_parenthesis=True)
        topics_part.append(s)

    # topics are joined with OR
    string = join_tokens_with_operator(topics_part, "OR", use_parenthesis=True)

    return string


def reduce_number_of_words_per_topic(
    topics: list[list[str]],
    n_words_per_topic: int,
) -> list[list[str]]:
    """Reduces the number of words in each topic.

    Args:
        topics (list[list[str]]): List with the topics.
        n_words_per_topic (int): Number of words to keep in each topic.

    Returns:
        List with the reduced topics.

    Examples:
        >>> reduce_number_of_words_per_topic([["machine", "learning"], ["code", "smell"]], 1)
        [['machine'], ['code']]
    """  # noqa: E501
    topics = [topic[:n_words_per_topic] for topic in topics]

    return topics
