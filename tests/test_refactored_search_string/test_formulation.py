import pytest
from sesg.search_string.formulation import (
    InvalidPubyearBoundariesError,
    join_tokens_with_operator,
    join_topics_with_similar_words,
    join_topics_without_similar_words,
    reduce_number_of_words_per_topic,
    set_pub_year_boundaries,
)


@pytest.mark.parametrize(
    "string,min_year,max_year,expected",
    [
        ("nlp", 1999, 2018, "nlp AND PUBYEAR > 1999 AND PUBYEAR < 2018"),
        ("nlp", 1999, None, "nlp AND PUBYEAR > 1999"),
        ("nlp", None, 2018, "nlp AND PUBYEAR < 2018"),
    ],
)
def test_set_pubyear_boundaries(
    string,
    min_year,
    max_year,
    expected,
):
    value = set_pub_year_boundaries(
        string=string,
        min_year=min_year,
        max_year=max_year,
    )

    assert value == expected


def test_set_pubyear_boundaries_should_raise_exception_when_min_year_is_greater_than_max_year():
    with pytest.raises(InvalidPubyearBoundariesError):
        set_pub_year_boundaries(
            string="string",
            min_year=2018,
            max_year=1999,
        )


@pytest.mark.parametrize(
    "tokens,operator,use_double_quotes,use_parenthesis,expected",
    [
        (
            ["machine", "learning", "computer"],
            "AND",
            False,
            False,
            "machine AND learning AND computer",
        ),
        (
            ["machine", "learning", "computer"],
            "OR",
            False,
            False,
            "machine OR learning OR computer",
        ),
        (
            ["machine", "learning", "computer"],
            "AND",
            True,
            False,
            '"machine" AND "learning" AND "computer"',
        ),
        (
            ["machine", "learning", "computer"],
            "OR",
            False,
            True,
            "(machine) OR (learning) OR (computer)",
        ),
        (
            ["machine", "learning", "computer"],
            "AND",
            True,
            True,
            '("machine") AND ("learning") AND ("computer")',
        ),
    ],
)
def test_join_tokens_with_operator(
    tokens,
    operator,
    use_double_quotes,
    use_parenthesis,
    expected,
):
    result = join_tokens_with_operator(
        tokens,
        operator,
        use_double_quotes=use_double_quotes,
        use_parenthesis=use_parenthesis,
    )

    assert result == expected


@pytest.mark.parametrize(
    "tokens,operator,use_double_quotes,use_parenthesis,expected",
    [
        (
            ["machine"],
            "AND",
            False,
            False,
            "machine",
        ),
        (
            ["machine"],
            "OR",
            False,
            False,
            "machine",
        ),
        (
            ["machine"],
            "AND",
            True,
            False,
            '"machine"',
        ),
        (
            ["machine"],
            "OR",
            False,
            True,
            "(machine)",
        ),
        (
            ["machine"],
            "AND",
            True,
            True,
            '("machine")',
        ),
    ],
)
def test_join_token_with_operator_should_return_only_token_when_list_has_one_element(
    operator,
    tokens,
    use_double_quotes,
    use_parenthesis,
    expected,
):
    result = join_tokens_with_operator(
        tokens,
        operator,
        use_double_quotes=use_double_quotes,
        use_parenthesis=use_parenthesis,
    )

    assert result == expected


@pytest.mark.parametrize(
    "topics,expected",
    [
        (
            [["machine", "learning"], ["defect", "detection"]],
            '("machine" AND "learning") OR ("defect" AND "detection")',
        ),
    ],
)
def test_join_topics_without_similar_words(
    topics,
    expected,
):
    result = join_topics_without_similar_words(topics)

    assert result == expected


@pytest.mark.parametrize(
    "topics,expected",
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
    topics,
    expected,
):
    result = join_topics_with_similar_words(topics)

    assert result == expected


@pytest.mark.parametrize(
    "topics,n_words_per_topic,expected",
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
    topics,
    n_words_per_topic,
    expected,
):
    result = reduce_number_of_words_per_topic(
        topics=topics,
        n_words_per_topic=n_words_per_topic,
    )

    assert result == expected
