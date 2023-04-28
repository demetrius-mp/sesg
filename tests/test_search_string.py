import pytest
from sesg import search_string


@pytest.fixture(scope="module")
def topics_list():
    return [
        [
            "software",
            "measurement",
            "gqm",
            "strategies",
            "goals",
            "organizational",
            "gqm strategies",
            "software measurement",
            "business",
            "level",
        ],
        [
            "process",
            "software",
            "strategic",
            "strategies",
            "improvement",
            "measurement",
            "organization",
            "goals",
            "process improvement",
            "engineering",
        ],
    ]


@pytest.mark.parametrize(
    "string,min_year,max_year,expected",
    [
        ("nlp", 1999, 2018, "nlp AND PUBYEAR > 1999 AND PUBYEAR < 2018"),
        ("nlp", 1999, None, "nlp AND PUBYEAR > 1999"),
        ("nlp", None, 2018, "nlp AND PUBYEAR < 2018"),
    ],
)
def test_set_pubyear(
    string,
    min_year,
    max_year,
    expected,
):
    value = search_string.set_pub_year(
        string=string,
        min_year=min_year,
        max_year=max_year,
    )

    assert value == expected


def test_generate_search_string_without_similar_words_with_1_topic_and_3_words_per_topic(
    topics_list: list[list[str]],
):
    result = search_string._generate_search_string_without_similar_words(
        topics_list=topics_list[:1],
        n_words_per_topic=3,
    )

    expected = '("software" AND "measurement" AND "gqm")'

    assert result == expected


def test_generate_search_string_without_similar_words_with_2_topics_and_5_words_per_topic(
    topics_list: list[list[str]],
):
    result = search_string._generate_search_string_without_similar_words(
        topics_list=topics_list,
        n_words_per_topic=5,
    )

    expected = '("software" AND "measurement" AND "gqm" AND "strategies" AND "goals") OR ("process" AND "software" AND "strategic" AND "strategies" AND "improvement")'

    assert result == expected
