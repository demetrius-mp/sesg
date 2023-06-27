"""Topic extraction with [BERTopic](https://arxiv.org/abs/2203.05794)."""

from bertopic import BERTopic  # type: ignore
from sklearn.cluster import KMeans  # type: ignore
from sklearn.feature_extraction.text import CountVectorizer  # type: ignore
from umap import UMAP  # type: ignore


def extract_topics_with_bertopic(
    docs: list[str],
    *,
    kmeans_n_clusters: int,
    umap_n_neighbors: int,
) -> list[list[str]]:
    """Extracts topics from a list of documents using BERTopic.

    Args:
        docs (list[str]): List of documents.
        kmeans_n_clusters (int): The number of clusters to form as well as the number of centroids to generate. This is equivalent to setting the number of topics.
        umap_n_neighbors (int): Number of neighboring sample points used when making the manifold approximation. Increasing this value typically results in a more global view of the embedding structure whilst smaller values result in a more local view. Increasing this value often results in larger clusters being created.

    Returns:
        List of topics, where a topic is a list of words.

    Examples:
        >>> extract_topics_with_bertopic(  # doctest: +SKIP
        ...     docs=["detecting code smells with machine learning", "code smells detection tools", "error detection in Java software with machine learning"],
        ... )
        [["word1 topic1", "word2 topic1"], ["word1 topic2", "word2 topic2"]]
    """  # noqa: E501
    vectorizer_model = CountVectorizer(
        stop_words="english",
        ngram_range=(1, 3),
    )

    umap_model = UMAP(
        n_neighbors=umap_n_neighbors,
        # default values used in BERTopic initialization.
        n_components=5,
        min_dist=0.0,
        metric="cosine",
        low_memory=False,
    )

    cluster_model = KMeans(
        n_clusters=kmeans_n_clusters,
    )

    topic_model = BERTopic(
        language="english",
        verbose=False,
        hdbscan_model=cluster_model,  # type: ignore
        vectorizer_model=vectorizer_model,
        umap_model=umap_model,
    )

    topic_model.fit_transform(docs)

    # topic_model.get_topics() will return a Mapping where
    # the key is the index of the topic,
    # and the value is a list of tuples
    # the tuple is composed of a word (or token), and its score

    topics: list[list[str]] = [
        [word for word, _ in topic_group]  # type: ignore
        for topic_group in topic_model.get_topics().values()
    ]

    return topics
