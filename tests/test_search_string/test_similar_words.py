import pytest
from sesg.search_string.similar_words import (
    _stemmed_similar_word_is_duplicate,
    _stemmed_similar_word_is_valid,
    _strings_are_close,
    _strings_are_distant,
    get_bert_similar_words,
    get_relevant_similar_words,
)

from .test_fixtures import enrichment_text, language_models


@pytest.fixture(scope="module")
def bert_similar_words(
    enrichment_text: str,
    language_models,
):
    bert_model, bert_tokenizer = language_models

    word = "software"

    result = get_bert_similar_words(
        "software",
        enrichment_text=enrichment_text,
        bert_model=bert_model,
        bert_tokenizer=bert_tokenizer,
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
    result = _strings_are_close(s1, s2)

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
    result = _strings_are_distant(s1, s2)

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
    result = _stemmed_similar_word_is_valid(
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
    result = _stemmed_similar_word_is_duplicate(
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
        "design",
        "##ized",
        "organizational",
        "business",
        "growth",
        "research",
        "strategy",
        "efficiency",
        "success",
        "effectiveness",
        "leadership",
        "transformation",
        "policy",
        "planning",
        "achievement",
        "action",
        "operational",
        "implementation",
        "sustainability",
        "unit",
        "process",
        "organization",
        "improvement",
        "managerial",
        "mission",
        "control",
    ]

    assert result == expected


def test_get_bert_similar_words_should_return_none_when_word_has_space(
    enrichment_text: str,
    language_models,
):
    bert_model, bert_tokenizer = language_models

    result = get_bert_similar_words(
        "multi organizational",
        enrichment_text=enrichment_text,
        bert_model=bert_model,
        bert_tokenizer=bert_tokenizer,
    )

    assert result is None


def test_get_bert_similar_words_should_return_none_when_word_is_not_in_enrichment_text(
    enrichment_text: str,
    language_models,
):
    bert_model, bert_tokenizer = language_models

    result = get_bert_similar_words(
        "biology",
        enrichment_text=enrichment_text,
        bert_model=bert_model,
        bert_tokenizer=bert_tokenizer,
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

    assert result == [
        "management",
        "development",
        "performance",
        "strategic",
        "design",
        "##ized",
        "business",
        "research",
        "efficiency",
        "success",
        "transformation",
        "achievement",
        "sustainability",
        "improvement",
        "control",
    ]
