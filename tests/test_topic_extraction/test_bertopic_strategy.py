import pytest
from sesg.topic_extraction import extract_topics_with_bertopic

from .test_fixtures import docs


@pytest.fixture(scope="module")
def bertopic_topics_with_2_clusters(
    docs: list[str],
):
    topics = extract_topics_with_bertopic(
        docs,
        umap_n_neighbors=3,
        kmeans_n_clusters=2,
    )

    return topics


def test_bertopic_topics_should_have_2_topics(
    bertopic_topics_with_2_clusters: list[list[str]],
):
    assert len(bertopic_topics_with_2_clusters) == 2


def test_each_bertopic_topic_should_have_at_least_10_entries(
    bertopic_topics_with_2_clusters: list[list[str]],
):
    for topic in bertopic_topics_with_2_clusters:
        assert len(topic) >= 10
