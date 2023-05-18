import pytest
from sesg.search_string.similar_words import (
    SimilarWordsFinder,
    _check_similar_word_is_relevant,
    _check_stemmed_similar_word_is_duplicate,
    _check_stemmed_similar_word_is_valid,
    _check_strings_are_close,
    _check_strings_are_distant,
    get_bert_similar_words,
    get_relevant_similar_words,
)

from .test_fixtures import similar_words_finder


@pytest.fixture(scope="module")
def bert_similar_words(
    similar_words_finder: SimilarWordsFinder,
):
    word = "software"

    result = get_bert_similar_words(
        "software",
        enrichment_text=similar_words_finder.enrichment_text,
        bert_model=similar_words_finder.bert_model,
        bert_tokenizer=similar_words_finder.bert_tokenizer,
    )

    return word, result


@pytest.mark.parametrize(
    "s1,s2,expected",
    [
        ("string", "strng", True),
        ("machine learning", "machine lerning", True),
    ],
)
def test_strings_are_close(
    s1,
    s2,
    expected,
):
    result = _check_strings_are_close(s1, s2)

    assert result == expected


@pytest.mark.parametrize(
    "s1,s2,expected",
    [
        ("string", "big string here", True),
        ("machine learning", "machine knowledge", True),
    ],
)
def test_strings_are_distant(
    s1,
    s2,
    expected,
):
    result = _check_strings_are_distant(s1, s2)

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
    result = _check_stemmed_similar_word_is_valid(
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
    result = _check_stemmed_similar_word_is_duplicate(
        stemmed_similar_word=stemmed_similar_word,
        stemmed_similar_words_list=stemmed_similar_words_list,
    )

    assert result == expected


def test_get_bert_similar_words(
    bert_similar_words: tuple[str, list[str]],
):
    _, result = bert_similar_words

    expected = [
        "management",
        "development",
        "performance",
        "strategic",
        "business",
        "research",
    ]

    assert set(expected).issubset(set(result))


def test_get_bert_similar_words_should_return_none_when_word_has_space(
    similar_words_finder: SimilarWordsFinder,
):
    result = get_bert_similar_words(
        "multi organizational",
        enrichment_text=similar_words_finder.enrichment_text,
        bert_model=similar_words_finder.bert_model,
        bert_tokenizer=similar_words_finder.bert_tokenizer,
    )

    assert result is None


def test_get_bert_similar_words_should_return_none_when_word_is_not_in_enrichment_text(
    similar_words_finder: SimilarWordsFinder,
):
    result = get_bert_similar_words(
        "biology",
        enrichment_text=similar_words_finder.enrichment_text,
        bert_model=similar_words_finder.bert_model,
        bert_tokenizer=similar_words_finder.bert_tokenizer,
    )

    assert result is None


def test_get_relevant_similar_words(
    bert_similar_words: tuple[str, list[str]],
):
    word, bert_similar_words_list = bert_similar_words

    result = get_relevant_similar_words(
        word,
        bert_similar_words_list=bert_similar_words_list,
    )

    expected = [
        "management",
        "development",
        "performance",
        "strategic",
        "business",
        "research",
    ]

    assert set(expected).issubset(set(result))


def test_get_relevant_similar_words_should_not_return_bert_oov_words(
    bert_similar_words: tuple[str, list[str]],
):
    word, bert_similar_words_list = bert_similar_words

    result = get_relevant_similar_words(
        word,
        bert_similar_words_list=bert_similar_words_list,
    )

    expected = [
        "management",
        "development",
        "performance",
        "strategic",
        "business",
        "research",
    ]

    assert set(expected).issubset(set(result))


def test_similar_words_finder_should_return_cached_value_when_key_was_used_previously(
    similar_words_finder: SimilarWordsFinder,
):
    result = similar_words_finder("software")

    if similar_words_finder.cache is None:
        raise RuntimeError("SimilarWordsFinder instance should have a cache")

    assert similar_words_finder.cache.get("software") == result


def test_similar_words_finder_should_return_none_when_key_was_never_used(
    similar_words_finder: SimilarWordsFinder,
):
    if similar_words_finder.cache is None:
        raise RuntimeError("SimilarWordsFinder instance should have a cache")

    assert similar_words_finder.cache.get("computer") is None


def test_check_similar_word_is_relevant_should_return_false_when_word_is_punctuation():
    assert (
        _check_similar_word_is_relevant(
            "-",
            stemmed_word="",
            stemmed_similar_word="",
            stemmed_relevant_similar_words=[],
        )
        is False
    )


def test_check_similar_word_is_relevant_should_return_false_when_word_is_bert_oov_word():
    assert (
        _check_similar_word_is_relevant(
            "##ization",
            stemmed_word="",
            stemmed_similar_word="",
            stemmed_relevant_similar_words=[],
        )
        is False
    )
