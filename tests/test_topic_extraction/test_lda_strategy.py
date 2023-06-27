import pytest
from sesg.topic_extraction import extract_topics_with_lda

from .test_fixtures import docs


@pytest.fixture(scope="module")
def lda_topics_with_min_document_frequency_04(
    docs: list[str],
):
    topics = extract_topics_with_lda(
        docs,
        min_document_frequency=0.4,
        n_topics=2,
    )

    return topics


def test_lda_topics_should_have_2_topics(
    lda_topics_with_min_document_frequency_04: list[list[str]],
):
    assert len(lda_topics_with_min_document_frequency_04) == 2


def test_each_lda_topic_should_have_at_least_10_entries(
    lda_topics_with_min_document_frequency_04: list[list[str]],
):
    for topic in lda_topics_with_min_document_frequency_04:
        assert len(topic) >= 10


def test_each_lda_topic_should_have_at_least_10_entries_even_with_high_document_frequency(
    lda_topics_with_min_document_frequency_04: list[list[str]],
):
    for topic in lda_topics_with_min_document_frequency_04:
        assert len(topic) >= 10
