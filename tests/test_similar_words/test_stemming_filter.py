import pytest
from sesg.similar_words.stemming_filter import (
    check_similar_word_is_relevant,
    check_stemmed_similar_word_is_duplicate,
    check_stemmed_similar_word_is_valid,
    check_strings_are_close,
    check_strings_are_distant,
    check_word_is_punctuation,
    filter_with_stemming,
)


@pytest.mark.parametrize(
    "s1,s2,expected",
    [
        ("computer", "computers", True),
        ("computer", "computation", False),
    ],
)
def test_strings_are_close(
    s1,
    s2,
    expected,
):
    result = check_strings_are_close(s1, s2)

    assert result == expected


@pytest.mark.parametrize(
    "s1,s2,expected",
    [
        ("string", "big string here", True),
        ("machine learning", "machine knowledge", True),
        ("machine learning", "machine learning", False),
    ],
)
def test_strings_are_distant(
    s1,
    s2,
    expected,
):
    result = check_strings_are_distant(s1, s2)

    assert result == expected


@pytest.mark.parametrize(
    "stemmed_similar_word,stemmed_word,expected",
    [
        ("word", "word", False),
        ("word", "worldwide", True),
    ],
)
def test_stemmed_similar_word_is_valid(
    stemmed_similar_word,
    stemmed_word,
    expected,
):
    result = check_stemmed_similar_word_is_valid(
        stemmed_similar_word=stemmed_similar_word,
        stemmed_word=stemmed_word,
    )

    assert result == expected


@pytest.mark.parametrize(
    "stemmed_similar_word,stemmed_similar_words_list,expected",
    [
        ("thing", ["things", "word"], True),
        ("tests", ["machine", "learning"], False),
    ],
)
def test_stemmed_similar_word_is_duplicate(
    stemmed_similar_word,
    stemmed_similar_words_list,
    expected,
):
    result = check_stemmed_similar_word_is_duplicate(
        stemmed_similar_word=stemmed_similar_word,
        stemmed_similar_words_list=stemmed_similar_words_list,
    )

    assert result == expected


@pytest.mark.parametrize(
    "word,expected",
    [
        ("-", True),
        ("--", False),
        ("*", True),
        ("word", False),
        ("software", False),
        ("software-", False),
        ("-software", False),
        ("-software-", False),
        ("-soft-ware-", False),
    ],
)
def test_check_word_is_punctuation_should_return_true_when_word_is_punctuation(
    word, expected
):
    result = check_word_is_punctuation(word)

    assert result is expected


def test_check_similar_word_is_relevant_should_return_false_when_word_is_punctuation():
    result = check_similar_word_is_relevant(
        "-",
        stemmed_word="",
        stemmed_similar_word="",
        stemmed_relevant_similar_words=[],
    )

    assert result is False


def test_check_similar_word_is_relevant_should_return_false_when_stemmed_word_is_not_valid():
    result = check_similar_word_is_relevant(
        "organizational",
        stemmed_word="organ",
        stemmed_similar_word="organ",
        stemmed_relevant_similar_words=[],
    )

    assert result is False


def test_check_similar_word_is_relevant_should_return_false_when_stemmed_word_is_duplicate():
    result = check_similar_word_is_relevant(
        "organization",
        stemmed_word="organ",
        stemmed_similar_word="organ",
        stemmed_relevant_similar_words=["organ"],
    )

    assert result is False


def test_filter_similar_words_with_stemming():
    result = filter_with_stemming(
        "organization",
        similar_words_list=[
            "organization",
            "organizational",
            "organize",
            "software",
            "process",
            "gqm+10",
            "computer",
        ],
    )

    assert result == [
        "process",
        "gqm+10",
        "computer",
    ]
