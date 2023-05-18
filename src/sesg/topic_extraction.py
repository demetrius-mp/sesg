"""Topic extraction module.

This module is responsible to provide topic extraction strategies.

Currently, the only available strategies are
[LDA (Latent Dirichlet Allocation)](https://www.jmlr.org/papers/volume3/blei03a/blei03a.pdf?ref=https://githubhelp.com),
and [BERTopic](https://arxiv.org/abs/2203.05794).
"""  # noqa: E501

from enum import Enum
from typing import Any, TypedDict

from sklearn.feature_extraction.text import CountVectorizer


class TopicExtractionStrategy(str, Enum):
    """Enum defining the available topic extraction strategies.

    Examples:
        >>> lda_strategy = TopicExtractionStrategy.lda
        >>> lda_strategy.value
        'lda'
    """

    lda = "lda"
    bertopic = "bertopic"


class DocStudy(TypedDict):
    """Data container for a study that will be used to generate a doc.

    Attributes:
        title (str): Title of the study.
        abstract (str): Abstract of the study.
        keywords (str): Keywords of the study.

    Examples:
        >>> study: DocStudy = {
        ...     "title": "machine learning",
        ...     "abstract": "machine learning is often used in the industry with the goal of...",
        ...     "keywords": "machine learning, code smells, defect detection"
        ... }
        >>> study
        {'title': 'machine learning', 'abstract': 'machine learning is often used in the industry with the goal of...', 'keywords': 'machine learning, code smells, defect detection'}
    """  # noqa: E501

    title: str
    abstract: str
    keywords: str


def _concat_study_info(
    study: DocStudy,
) -> str:
    r"""Concatenates the information of the study into a string.

    Args:
        study (DocStudy): Study with title, abstract and keywords.

    Returns:
        A string with the following format: "{title}\n{abstract}\n{keywords}".

    Examples:
        >>> study: DocStudy = {
        ...     "title": "machine learning",
        ...     "abstract": "machine learning is often used in the industry with the goal of...",
        ...     "keywords": "machine learning, code smells, defect detection"
        ... }
        >>> _concat_study_info(study)
        'machine learning\nmachine learning is often used in the industry with the goal of...\nmachine learning, code smells, defect detection'
    """  # noqa: E501
    title = study["title"]
    abstract = study["abstract"]
    keywords = study["keywords"]

    return f"{title}\n{abstract}\n{keywords}"


def create_docs(
    studies_list: list[DocStudy],
) -> list[str]:
    r"""Creates a list of documents where each document is a string with the title, abstract and keywords of the study.

    Can be used with [extract_topics_with_lda][sesg.topic_extraction.extract_topics_with_lda] or [extract_topics_with_bertopic][sesg.topic_extraction.extract_topics_with_bertopic].

    Args:
        studies_list (list[DocStudy]): List of studies with title, abstract and keywords.

    Returns:
        List of documents.

    Examples:
        >>> s1: DocStudy = {
        ...     "title": "machine learning",
        ...     "abstract": "machine learning is often used in the industry with the goal of...",
        ...     "keywords": "machine learning, code smells, defect detection"
        ... }
        >>> s2: DocStudy = {
        ...     "title": "artificial intelligence",
        ...     "abstract": "artificial intelligence is often used in the industry with the goal of...",
        ...     "keywords": "artificial intelligence, code smells, defect detection"
        ... }
        >>> create_docs([s1, s2])
        ['machine learning\nmachine learning is often used in the industry with the goal of...\nmachine learning, code smells, defect detection', 'artificial intelligence\nartificial intelligence is often used in the industry with the goal of...\nartificial intelligence, code smells, defect detection']
    """  # noqa: E501
    return [_concat_study_info(s) for s in studies_list]


def extract_topics_with_lda(
    docs: list[str],
    *,
    min_document_frequency: float,
    n_topics: int,
) -> list[list[str]]:
    """Extracts topics from a list of documents using LDA method.

    Args:
        docs (list[str]): List of documents.
        min_document_frequency (float): CountVectorizer parameter - Minimum document frequency for the word to appear on the bag of words.
        n_topics (int): LDA parameter - Number of topics to generate.

    Returns:
        list of topics, where a topic is a list of words.

    Examples:
        >>> extract_topics_with_lda(  # doctest: +SKIP
        ...     docs=["detecting code smells with machine learning", "code smells detection tools", "error detection in Java software with machine learning"],
        ...     min_document_frequency=0.1,
        ...     n_topics=2,
        ... )
        [["word1 topic1", "word2 topic1"], ["word1 topic2", "word2 topic2"]]
    """  # noqa: E501
    from sklearn.decomposition import LatentDirichletAllocation

    # without this "Any typings", pylance takes too long to analyze the sklearn files
    # remove this line once sklearn has developed stubs for the package
    LatentDirichletAllocation: Any

    vectorizer = CountVectorizer(
        min_df=min_document_frequency,
        max_df=1.0,
        ngram_range=(1, 3),
        max_features=None,
        stop_words="english",
    )

    tf = vectorizer.fit_transform(docs)

    # `feature_names` is a list with the vectorized words from the document.
    # meaning `feature_names[i]` is a token in the text.
    feature_names = vectorizer.get_feature_names_out()

    alpha = None
    beta = None
    learning = "batch"  # Batch or Online

    # Run the Latent Dirichlet Allocation (LDA) algorithm and train it.
    lda = LatentDirichletAllocation(
        n_components=n_topics,
        doc_topic_prior=alpha,
        topic_word_prior=beta,
        learning_method=learning,
        learning_decay=0.7,
        learning_offset=10.0,
        max_iter=5000,
        batch_size=128,
        evaluate_every=-1,
        total_samples=1000000.0,
        perp_tol=0.1,
        mean_change_tol=0.001,
        max_doc_update_iter=100,
        random_state=0,
    )

    lda.fit(tf)

    # `lda.components_` hold the entire list of topics found by LDA.
    # notice that for `lda.components_`, the topic is a list of indexes
    # where the index will map to a token (~word) in `feature_names`.
    # as an example, the next line gets all tokens of the first topic

    # first_topic = lda.components_[0]
    # topic_words = [feature_names[i] for i in first_topic]

    # `topic.argsort()` will return the indexes that would sort the topics,
    # in ascending order
    # since we want the most latent topics, we reverse the list with `[::-1]`

    topics: list[list[str]] = [
        [feature_names[i] for i in topic.argsort()[::-1]] for topic in lda.components_
    ]

    return topics


def extract_topics_with_bertopic(
    docs: list[str],
    *,
    kmeans_n_clusters: int,
    umap_n_neighbors: int,
) -> list[list[str]]:
    """Extracts topics from a list of documents using BERTopic.

    Args:
        docs (list[str]): List of documents.
        kmeans_n_clusters (int): The number of clusters to form as well as the number of centroids to generate.
        umap_n_neighbors (int): Number of neighboring sample points used when making the manifold approximation. Increasing this value typically results in a more global view of the embedding structure whilst smaller values result in a more local view. Increasing this value often results in larger clusters being created.

    Returns:
        List of topics, where a topic is a list of words.

    Examples:
        >>> extract_topics_with_bertopic(  # doctest: +SKIP
        ...     docs=["detecting code smells with machine learning", "code smells detection tools", "error detection in Java software with machine learning"],
        ... )
        [["word1 topic1", "word2 topic1"], ["word1 topic2", "word2 topic2"]]
    """  # noqa: E501
    from bertopic import BERTopic
    from sklearn.cluster import KMeans
    from umap import UMAP

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
