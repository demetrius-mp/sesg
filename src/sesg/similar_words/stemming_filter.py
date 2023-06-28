"""Filter out similar words that are too similar character-wise based on stemming.

Attributes:
    PUNCTUATION (set[str]): Set of punctuation characters. Defaults to `#!python set(string.punctuation)`.
"""  # noqa: E501

from string import punctuation

from nltk.stem import LancasterStemmer  # type: ignore
from rapidfuzz.distance import Levenshtein


PUNCTUATION: set[str] = set(punctuation)


lancaster = LancasterStemmer()


def check_strings_are_distant(
    s1: str,
    s2: str,
) -> bool:
    """Checks if the given strings have at least 5 units of levenshtein distance.

    Args:
        s1 (str): First string.
        s2 (str): Second string.

    Returns:
        True if the strings have at least 4 units of levenshtein distance, False otherwise.

    Examples:
        >>> check_strings_are_distant("string", "string12345")
        True
        >>> check_strings_are_distant("string", "strng")
        False
    """  # noqa: E501
    levenshtein_distance = 4
    return Levenshtein.distance(str(s1), str(s2)) > levenshtein_distance


def check_strings_are_close(
    s1: str,
    s2: str,
) -> bool:
    """Checks if the given strings have at most 3 units of levenshtein distance.

    Args:
        s1 (str): First string.
        s2 (str): Second string.

    Returns:
        True if the strings have at most 3 units of levenshtein distance, False otherwise.

    Examples:
        >>> check_strings_are_close("string", "big string")
        False
        >>> check_strings_are_close("string", "strng")
        True
    """  # noqa: E501
    levenshtein_distance = 4
    return Levenshtein.distance(str(s1), str(s2)) < levenshtein_distance


def check_stemmed_similar_word_is_valid(
    stemmed_similar_word: str,
    *,
    stemmed_word: str,
) -> bool:
    """Checks if the stemmed similar word is valid.

    A stemmed similar word is considered valid if it complies the following criteria:

    - It is not equal to the stemmed word
    - It is distant from the stemmed word (see [check_strings_are_distant][sesg.similar_words.stemming_filter.check_strings_are_distant]).

    Args:
        stemmed_similar_word (str): The stemmed similar word.
        stemmed_word (str): The word itself.

    Returns:
        True if the strings are not equal and distant, False otherwise.

    Examples:
        >>> check_stemmed_similar_word_is_valid(
        ...     "string",
        ...     stemmed_word="string"
        ... )
        False
        >>> check_stemmed_similar_word_is_valid(
        ...     "string",
        ...     stemmed_word="stringified"
        ... )
        True
    """  # noqa: E501
    not_equal = stemmed_word != stemmed_similar_word
    distant = check_strings_are_distant(stemmed_similar_word, stemmed_word)

    return not_equal and distant


def check_stemmed_similar_word_is_duplicate(
    stemmed_similar_word: str,
    *,
    stemmed_similar_words_list: list[str],
) -> bool:
    """Checks if the stemmed similar word is a duplicate.

    A stemmed similar word is considered duplicate if it is close to one of the stemmed similar word in the list.

    Args:
        stemmed_similar_word (str): The stemmed similar word.
        stemmed_similar_words_list (list[str]): List of stemmed words to check against.

    Returns:
        True if the stemmed similar word is a duplicate, False otherwise.

    Examples:
        >>> check_stemmed_similar_word_is_duplicate(
        ...     "string",
        ...     stemmed_similar_words_list=["other", "somewhat"],
        ... )
        False
        >>> check_stemmed_similar_word_is_duplicate(
        ...     "string",
        ...     stemmed_similar_words_list=["strng", "something"],
        ... )
        True
    """  # noqa: E501
    for word in stemmed_similar_words_list:
        is_close = check_strings_are_close(word, stemmed_similar_word)
        if is_close:
            return True

    return False


def check_word_is_punctuation(
    word: str,
) -> bool:
    """Checks if the given word is not punctuation.

    This function uses `#!python string.punctuation` to get punctuation characters.

    Args:
        word (str): Word to check.

    Returns:
        True if the word is punctuation, False otherwise.

    Examples:
        >>> check_word_is_punctuation("a")
        False
        >>> check_word_is_punctuation(">")
        True
    """
    return word in PUNCTUATION


def check_similar_word_is_relevant(
    similar_word: str,
    *,
    stemmed_word: str,
    stemmed_similar_word: str,
    stemmed_relevant_similar_words: list[str],
) -> bool:
    """Checks if the given similar word is relevant.

    A similar word is considered relevant if it complies the following criteria, in order:

    - It is not a punctuation character (see [check_word_is_punctuation][sesg.similar_words.stemming_filter.check_word_is_punctuation]).
    - It's stemmed form is valid (see [check_stemmed_similar_word_is_valid][sesg.similar_words.stemming_filter.check_stemmed_similar_word_is_valid]).
    - It's stemmed form is not a duplicate (see [check_stemmed_similar_word_is_duplicate][sesg.similar_words.stemming_filter.check_stemmed_similar_word_is_duplicate]).

    Args:
        similar_word (str): Similar word to check if is relevant.
        stemmed_word (str): Stemmed form of the original word.
        stemmed_similar_word (str): Stemmed form of the similar word.
        stemmed_relevant_similar_words (list[str]): List of stemmed relevant similar words to check for duplicates.

    Returns:
        True if the similar word is relevant, False otherwise.
    """  # noqa: E501
    is_punctuation = check_word_is_punctuation(similar_word)
    if is_punctuation:
        return False

    is_valid = check_stemmed_similar_word_is_valid(
        stemmed_similar_word,
        stemmed_word=stemmed_word,
    )
    if not is_valid:
        return False

    is_duplicate = check_stemmed_similar_word_is_duplicate(
        stemmed_similar_word,
        stemmed_similar_words_list=stemmed_relevant_similar_words,
    )
    if is_duplicate:
        return False

    return True


def filter_with_stemming(
    word: str,
    *,
    similar_words_list: list[str],
) -> list[str]:
    """Filters out similar words that are not relevant.

    A similar word is kept on the list if it complies the following criteria:

    - It is not a punctuation character (see [check_word_is_punctuation][sesg.similar_words.stemming_filter.check_word_is_punctuation]).
    - It's stemmed form is valid (see [check_stemmed_similar_word_is_valid][sesg.similar_words.stemming_filter.check_stemmed_similar_word_is_valid]).
    - It's stemmed form is not a duplicate (see [check_stemmed_similar_word_is_duplicate][sesg.similar_words.stemming_filter.check_stemmed_similar_word_is_duplicate]).

    Args:
        word (str): Word that was used to generate the similar ones.
        similar_words_list (list[str]): List with the similar words.

    Returns:
        List of filtered similar words.
    """  # noqa: E501
    stemmed_word: str = lancaster.stem(word)

    # list with the filtered similar words
    relevant_similar_words: list[str] = []

    # list with the filtered similar words, but stemmed
    stemmed_relevant_similar_words: list[str] = []

    for similar_word in similar_words_list:
        stemmed_similar_word = lancaster.stem(similar_word)

        similar_word_is_relevant = check_similar_word_is_relevant(
            similar_word,
            stemmed_word=stemmed_word,
            stemmed_similar_word=stemmed_similar_word,
            stemmed_relevant_similar_words=stemmed_relevant_similar_words,
        )

        if not similar_word_is_relevant:
            continue

        relevant_similar_words.append(similar_word)
        stemmed_relevant_similar_words.append(stemmed_similar_word)

    return relevant_similar_words
