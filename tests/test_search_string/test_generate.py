import pytest
from sesg.search_string.generate import (
    _generate_search_string_with_similar_words,
    _generate_search_string_without_similar_words,
    _join_tokens_with_operator,
    _join_topics_with_similar_words,
    _join_topics_without_similar_words,
    _reduce_number_of_words_per_topic,
    generate_search_string,
)
from sesg.search_string.similar_words import SimilarWordsFinder

from .test_fixtures import similar_words_finder


@pytest.mark.parametrize(
    "operator,tokens_list,use_double_quotes,use_parenthesis,expected",
    [
        (
            "AND",
            ["machine", "learning", "computer"],
            False,
            False,
            "machine AND learning AND computer",
        ),
        (
            "OR",
            ["machine", "learning", "computer"],
            False,
            False,
            "machine OR learning OR computer",
        ),
        (
            "AND",
            ["machine", "learning", "computer"],
            True,
            False,
            '"machine" AND "learning" AND "computer"',
        ),
        (
            "OR",
            ["machine", "learning", "computer"],
            False,
            True,
            "(machine) OR (learning) OR (computer)",
        ),
        (
            "AND",
            ["machine", "learning", "computer"],
            True,
            True,
            '("machine") AND ("learning") AND ("computer")',
        ),
    ],
)
def test_join_tokens_with_operator(
    operator,
    tokens_list,
    use_double_quotes,
    use_parenthesis,
    expected,
):
    result = _join_tokens_with_operator(
        operator,
        tokens_list,
        use_double_quotes=use_double_quotes,
        use_parenthesis=use_parenthesis,
    )

    assert result == expected


@pytest.mark.parametrize(
    "operator,tokens_list,use_double_quotes,use_parenthesis,expected",
    [
        (
            "AND",
            ["machine"],
            False,
            False,
            "machine",
        ),
        (
            "OR",
            ["machine"],
            False,
            False,
            "machine",
        ),
        (
            "AND",
            ["machine"],
            True,
            False,
            '"machine"',
        ),
        (
            "OR",
            ["machine"],
            False,
            True,
            "(machine)",
        ),
        (
            "AND",
            ["machine"],
            True,
            True,
            '("machine")',
        ),
    ],
)
def test_join_token_with_operator_should_return_only_token_when_list_has_one_element(
    operator,
    tokens_list,
    use_double_quotes,
    use_parenthesis,
    expected,
):
    result = _join_tokens_with_operator(
        operator,
        tokens_list,
        use_double_quotes=use_double_quotes,
        use_parenthesis=use_parenthesis,
    )

    assert result == expected


@pytest.mark.parametrize(
    "topics_list,expected",
    [
        (
            [["machine", "learning"], ["defect", "detection"]],
            '("machine" AND "learning") OR ("defect" AND "detection")',
        ),
    ],
)
def test_join_topics_without_similar_words(
    topics_list,
    expected,
):
    result = _join_topics_without_similar_words(topics_list)

    assert result == expected


@pytest.mark.parametrize(
    "topics_list,expected",
    [
        (
            [
                [["machine", "computer"], ["learning", "knowledge"]],
                [["defect", "error"], ["detection", "finder"]],
            ],
            '(("machine" OR "computer") AND ("learning" OR "knowledge")) OR (("defect" OR "error") AND ("detection" OR "finder"))',
        ),
    ],
)
def test_join_topics_with_similar_words(
    topics_list,
    expected,
):
    result = _join_topics_with_similar_words(topics_list)

    assert result == expected


@pytest.mark.parametrize(
    "topics_list,n_words_per_topic,expected",
    [
        (
            [["t11", "t12", "t13"], ["t21", "t22", "t23"]],
            2,
            [["t11", "t12"], ["t21", "t22"]],
        ),
        (
            [["t11", "t12", "t13"], ["t21", "t22", "t23"]],
            1,
            [["t11"], ["t21"]],
        ),
    ],
)
def test_reduce_number_of_words_per_topic(
    topics_list,
    n_words_per_topic,
    expected,
):
    result = _reduce_number_of_words_per_topic(
        topics_list=topics_list,
        n_words_per_topic=n_words_per_topic,
    )

    assert result == expected


@pytest.mark.parametrize(
    "topics_list,n_words_per_topic,expected",
    [
        (
            [["t11", "t12", "t13"], ["t21", "t22", "t23"]],
            2,
            '("t11" AND "t12") OR ("t21" AND "t22")',
        ),
        (
            [["t11", "t12", "t13"], ["t21", "t22", "t23"]],
            3,
            '("t11" AND "t12" AND "t13") OR ("t21" AND "t22" AND "t23")',
        ),
    ],
)
def test_generate_search_string_without_similar_words(
    topics_list,
    n_words_per_topic,
    expected,
):
    result = _generate_search_string_without_similar_words(
        topics_list=topics_list,
        n_words_per_topic=n_words_per_topic,
    )

    assert result == expected


def test_generate_search_string_with_similar_words(
    similar_words_finder: SimilarWordsFinder,
):
    result = _generate_search_string_with_similar_words(
        topics_list=[
            ["software", "measurement", "gqm"],
            ["process", "software", "strategic"],
        ],
        n_similar_words_per_word=2,
        n_words_per_topic=2,
        similar_words_finder=similar_words_finder,
    )
    expected = '(("software" OR "management" OR "development") AND ("measurement" OR "development" OR "design")) OR (("process" OR "software" OR "business") AND ("software" OR "management" OR "development"))'

    assert result == expected


def test_generate_search_string_with_0_similar_words_should_return_result_of_generate_search_string_without_similar_words(
    similar_words_finder: SimilarWordsFinder,
):
    n_words_per_topic = 2

    result = generate_search_string(
        topics_list=[
            ["software", "measurement", "gqm"],
            ["process", "software", "strategic"],
        ],
        n_words_per_topic=n_words_per_topic,
        n_similar_words=0,
        similar_words_finder=similar_words_finder,
    )

    expected = _generate_search_string_without_similar_words(
        topics_list=[
            ["software", "measurement", "gqm"],
            ["process", "software", "strategic"],
        ],
        n_words_per_topic=n_words_per_topic,
    )

    assert result == expected


def test_generate_search_string_with_2_similar_words_should_return_result_of_generate_search_string_with_similar_words(
    similar_words_finder: SimilarWordsFinder,
):
    n_words_per_topic = 2

    result = generate_search_string(
        topics_list=[
            ["software", "measurement", "gqm"],
            ["process", "software", "strategic"],
        ],
        n_words_per_topic=n_words_per_topic,
        n_similar_words=2,
        similar_words_finder=similar_words_finder,
    )

    expected = _generate_search_string_with_similar_words(
        topics_list=[
            ["software", "measurement", "gqm"],
            ["process", "software", "strategic"],
        ],
        n_similar_words_per_word=2,
        n_words_per_topic=n_words_per_topic,
        similar_words_finder=similar_words_finder,
    )

    assert result == expected
