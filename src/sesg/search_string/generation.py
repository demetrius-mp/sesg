"""Search string generation."""


from sesg.similar_words.protocol import SimilarWordsGenerator
from sesg.similar_words.stemming_filter import filter_with_stemming

from .formulation import (
    join_topics_with_similar_words,
    join_topics_without_similar_words,
    reduce_number_of_words_per_topic,
)


def generate_search_string_without_similar_words(
    *,
    topics: list[list[str]],
    n_words_per_topic: int,
) -> str:
    """Generates a search string by reducing the number of topics, and joining the reduced topics.

    Words from the same topic are joined with `AND`, and topics are joined with `OR`.

    Args:
        topics (list[list[str]]): List of topics to use.
        n_words_per_topic (int): Number of words to keep in each topic.

    Returns:
        The search string.
    """  # noqa: E501
    topics = reduce_number_of_words_per_topic(
        topics=topics,
        n_words_per_topic=n_words_per_topic,
    )

    string = join_topics_without_similar_words(topics)

    return string


def generate_search_string_with_similar_words(
    topics: list[list[str]],
    n_words_per_topic: int,
    n_similar_words_per_word: int,
    similar_words_generator: SimilarWordsGenerator,
) -> str:
    """Generates a search string with the following steps.

    1. Reduces the number of words per topic.
    1. For each word in each topic, finds similar words with the given function.

    Args:
        topics (list[list[str]]): List of topics to use.
        n_words_per_topic (int): Number of words to keep in each topic.
        n_similar_words_per_word (int): Number of similar words to generate for each word in each topic.
        similar_words_generator (SimilarWordsGenerator): Instance of SimilarWordsGenerator.

    Returns:
        The search string.
    """  # noqa: E501
    topics_list = reduce_number_of_words_per_topic(
        topics=topics,
        n_words_per_topic=n_words_per_topic,
    )

    topics_with_similar_words: list[list[list[str]]] = []

    for topic in topics_list:
        topic_part: list[list[str]] = []
        for token in topic:
            similar_words = similar_words_generator(token)
            similar_words = filter_with_stemming(
                token,
                similar_words_list=similar_words,
            )

            # limiting the number of similar words
            # we add one because the word itself is included in the similar_words list
            word_with_similar_words = [token, *similar_words[:n_similar_words_per_word]]
            topic_part.append(word_with_similar_words)

        topics_with_similar_words.append(topic_part)

    string = join_topics_with_similar_words(topics_with_similar_words)

    return string


def generate_search_string(
    topics: list[list[str]],
    n_words_per_topic: int,
    *,
    n_similar_words_per_word: int = 0,
    similar_words_generator: SimilarWordsGenerator | None = None,
) -> str:
    """Generates a search string that will be enriched with the desired number of similar words.

    Args:
        topics (list[list[str]]): List of topics to use.
        n_words_per_topic (int): Number of words to keep in each topic.
        n_similar_words_per_word (int): Number of similar words to generate for each word in each topic.
        similar_words_generator (SimilarWordsFinder): Instance of SimilarWordsFinder.

    Returns:
        A search string.
    """  # noqa: E501
    if n_similar_words_per_word == 0:
        return generate_search_string_without_similar_words(
            topics=topics,
            n_words_per_topic=n_words_per_topic,
        )

    if similar_words_generator is None:
        raise ValueError(
            "similar_words_generator must be provided if n_similar_words_per_word > 0"
        )

    return generate_search_string_with_similar_words(
        topics=topics,
        n_words_per_topic=n_words_per_topic,
        n_similar_words_per_word=n_similar_words_per_word,
        similar_words_generator=similar_words_generator,
    )
