from enum import Enum
from typing import Any, List

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


def extract_topics_with_lda(
    docs: List[str],
    min_document_frequency: float,
    number_of_topics: int,
) -> List[List[str]]:
    """Extracts topics from a list of documents using LDA method.

    Args:
        docs (List[str]): List of documents.
        min_document_frequency (float): CountVectorizer parameter - Minimum document frequency for the word to appear on the bag of words.
        number_of_topics (int): LDA parameter - Number of topics to generate.

    Returns:
        List of topics, where a topic is a list of words.

    Examples:
        >>> extract_topics_with_lda(  # doctest: +SKIP
        ...     docs=["detecting code smells with machine learning", "code smells detection tools", "error detection in Java software with machine learning"],
        ...     min_document_frequency=0.1,
        ...     number_of_topics=2,
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
        n_components=number_of_topics,
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

    topics: List[List[str]] = [
        [feature_names[i] for i in topic.argsort()[::-1]] for topic in lda.components_
    ]

    return topics


def extract_topics_with_bertopic(
    docs: List[str],
) -> List[List[str]]:
    """Extracts topics from a list of documents using BERTopic.

    Args:
        docs (List[str]): List of documents.

    Returns:
        List of topics, where a topic is a list of words.

    Examples:
        >>> extract_topics_with_bertopic(  # doctest: +SKIP
        ...     docs=["detecting code smells with machine learning", "code smells detection tools", "error detection in Java software with machine learning"],
        ... )
        [["word1 topic1", "word2 topic1"], ["word1 topic2", "word2 topic2"]]
    """  # noqa: E501
    from bertopic import BERTopic

    vectorizer_model = CountVectorizer(
        stop_words="english",
        ngram_range=(1, 3),
    )

    topic_model = BERTopic(
        language="english",
        verbose=True,
        min_topic_size=2,
        vectorizer_model=vectorizer_model,
    )

    topic_model.fit_transform(docs)

    # topic_model.get_topics() will return a Mapping where
    # the key is the index of the topic,
    # and the value is a list of tuples
    # the tuple is composed of a word (or token), and its score

    topics: List[List[str]] = [
        [word for word, _ in topic_group]  # type: ignore
        for topic_group in topic_model.get_topics().values()
    ]

    return topics