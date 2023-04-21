"""Search String module.

This module is responsible to mount the search string. We use BERT's
token prediction with the goal of obtaining similar words, and use them
enrich the final string.
"""  # noqa: E501

from typing import Any, List, Optional, TypedDict, Union

from rapidfuzz.distance import Levenshtein


def _enrich_word(
    *,
    word: str,
    enrichment_text: str,
    bert_tokenizer: Any,
    bert_model: Any,
) -> Union[List[str], None]:
    """Tries to find words that are similar to the target word using the enrichment text.

    Args:
        word (str): Word to which other similar ones will be generated.
        enrichment_text (str): Text that will be used to find similar words.
        bert_tokenizer: A BERT tokenizer.
        bert_model: A BERT model.

    Returns:
        List of similar words, or None if the word.
    """  # noqa: E501
    import numpy as np
    import torch

    selected_sentences: List[str] = []

    # Treatment for if the selected sentence is the last sentence of the text (return only one sentence).  # noqa: E501
    for sentence in enrichment_text.split("."):
        if word in sentence or word in sentence.lower():
            selected_sentences.append(sentence + ".")
            break

    formated_sentences = "[CLS] "
    for sentence in selected_sentences:
        formated_sentences += sentence.lower() + " [SEP] "

    tokenized_text = bert_tokenizer.tokenize(formated_sentences)

    # Defining the masked index equal to the word of the input.
    masked_index = 0
    word_is_in_tokens = False

    for count, token in enumerate(tokenized_text):
        if word in token.lower():
            masked_index = count
            tokenized_text[masked_index] = "[MASK]"

            word_is_in_tokens = True

    if not word_is_in_tokens:
        return None

    # Convert token to vocabulary indices.
    indexed_tokens = bert_tokenizer.convert_tokens_to_ids(tokenized_text)

    # Define sentence A and B indices associated to first and second sentences.
    len_first = tokenized_text.index("[SEP]")
    len_first = len_first + 1
    segments_ids = [0] * len_first + [1] * (len(tokenized_text) - len_first)

    # Convert the inputs to PyTorch tensors.
    tokens_tensor = torch.tensor([indexed_tokens])
    segments_tensors = torch.tensor([segments_ids])

    # Predict all tokens.
    with torch.no_grad():
        outputs = bert_model(tokens_tensor, token_type_ids=segments_tensors)
        predictions = outputs[0]

    # Predict the thirty first possibilities of the word masked.
    predicted_index = torch.topk(predictions[0, masked_index], 30)[1]
    predicted_index = list(np.array(predicted_index))

    # Remove the \2022 ascii error index.
    for index in predicted_index:
        if index == "1528":
            predicted_index.remove("1528")

    for index in predicted_index:
        if index == 1000:
            predicted_index.remove(1000)

    predicted_tokens = bert_tokenizer.convert_ids_to_tokens(predicted_index)

    return predicted_tokens


class EnrichmentStudy(TypedDict):
    """Data container for a study that will be used to generate an enrichment text.

    Attributes:
        title (str): Title of the study.
        abstract (str): Abstract of the study.

    Examples:
        >>> study: EnrichmentStudy = {
        ...     "title": "machine learning",
        ...     "abstract": "machine learning is often used in the industry with the goal of...",
        ... }
        >>> study
        {'title': 'machine learning', 'abstract': 'machine learning is often used in the industry with the goal of...'}
    """  # noqa: E501

    title: str
    abstract: str


def generate_enrichment_text(
    *,
    studies_list: List[EnrichmentStudy],
) -> str:
    r"""Generates a piece of text that consists of the concatenation of the title and abstract of each study.

    Can be used with the [`sesg.search_string.generate_search_string`][] function.

    Args:
        studies_list (List[EnrichmentStudy]): List of studies with title and abstract.

    Returns:
        The enrichment text.

    Examples:
        >>> studies = [
        ...     EnrichmentStudy(title="title1", abstract="abstract1"),
        ...     EnrichmentStudy(title="title2", abstract="abstract2 \r\ntext"),
        ...     EnrichmentStudy(title="title3", abstract="abstract3"),
        ... ]
        >>> generate_enrichment_text(studies_list=studies)
        'title1 abstract1\ntitle2 abstract2 #.text\ntitle3 abstract3\n'
    """  # noqa: E501
    enrichment_text = ""
    for study in studies_list:
        title = study["title"]
        abstract = study["abstract"]

        line = f"{title} {abstract}".strip().replace("\r\n", "#.") + "\n"
        enrichment_text += line

    return enrichment_text


def _generate_search_string_without_similar_words(
    *,
    topics_list: List[List[str]],
    n_words_per_topic: int,
) -> str:
    """Generates a search string using the given list of topics.

    Args:
        topics_list (List[List[str]]): List of topics, where each topic is a list of words.
        n_words_per_topic (int): Indicates how many words of each topic will be inserted into the string.

    Returns:
        A search string.
    """  # noqa: E501
    string = ""

    for topic_index, topic in enumerate(topics_list):
        words_of_topic = topic[:n_words_per_topic]

        string += '("'
        string += '" AND "'.join(words_of_topic)
        string += '")'

        if topic_index != len(topics_list) - 1:
            string += " OR "

    return string


def _generate_search_string_with_similar_words(
    *,
    topics_list: List[List[str]],
    n_words_per_topic: int,
    n_similar_words: int,
    enrichment_text: str,
    bert_tokenizer: Any,
    bert_model: Any,
) -> str:
    """Generates a search string that will be enriched with the desired number of similar words.

    Args:
        topics_list (List[List[str]]): List of topics, where each topic is a list of words.
        n_words_per_topic (int): Indicates how many words of each topic will be inserted into the string.
        n_similar_words (int): Number of similar words to generate for each word in each topic.
        enrichment_text (str): The text to use to enrich each word.
        bert_tokenizer: A BERT tokenizer.
        bert_model: A BERT model.

    Returns:
        A search string.
    """  # noqa: E501
    from nltk.stem import LancasterStemmer

    levenshtein_distance = 4
    string = ""

    lancaster = LancasterStemmer()

    for topic_index, topic in enumerate(topics_list):
        counter = 0
        string += "("

        for topic_word in topic[:n_words_per_topic]:
            counter = counter + 1

            string += '("'
            string += '" - "'.join([topic_word])

            if " " not in topic_word:
                list_of_similar_words = _enrich_word(
                    word=topic_word,
                    enrichment_text=enrichment_text,
                    bert_tokenizer=bert_tokenizer,
                    bert_model=bert_model,
                )

                # Error if the word searched it's not presented in the tokens
                if list_of_similar_words is None:
                    pass
                else:
                    stemmed_topic_word: str = lancaster.stem(topic_word)

                    final_stemmed_similar_words: List[str] = []
                    final_similar_words: List[str] = []

                    # this loop is responsible to filter out the generated similar words
                    # that are similar to each other.
                    for similar_word_index, similar_word in enumerate(
                        list_of_similar_words
                    ):
                        stemmed_similar_word: str = lancaster.stem(similar_word)

                        # Checks if the stemmed topic word and the stemmed similar word
                        # are at least 40% different (actually at least 4 units in Levenshtein Distance).  # noqa: E501
                        # This actually checks if the current topic word is somewhat
                        # different from the current similar word
                        if (
                            stemmed_topic_word != stemmed_similar_word
                            and Levenshtein.distance(
                                str(stemmed_topic_word), str(stemmed_similar_word)
                            )
                            > levenshtein_distance
                        ):
                            # if we passed the above condition, we can assure that
                            # the current similar word is different from the current topic word  # noqa: E501

                            # now, we need to make sure that the current similar word
                            # is different from previous similar words

                            # if the stemmed word is similar to any of the previous
                            # stemmed words, it will not be included in the final list
                            # of similar words.
                            # This actually avoids adding similar words that are too similar.  # noqa: E501
                            similar_word_is_relevant = True
                            for old_stemmed_similar_word in final_stemmed_similar_words:
                                if (
                                    Levenshtein.distance(
                                        str(old_stemmed_similar_word),
                                        str(stemmed_similar_word),
                                    )
                                    < levenshtein_distance
                                ):
                                    similar_word_is_relevant = False

                            if similar_word_is_relevant:
                                final_stemmed_similar_words.append(stemmed_similar_word)
                                final_similar_words.append(
                                    list_of_similar_words[similar_word_index]
                                )

                    string += '" OR "'
                    if len(final_similar_words) < n_similar_words:
                        string += '" OR "'.join(
                            final_similar_words[m]
                            for m in range(0, len(final_similar_words))
                        )
                    else:
                        string += '" OR "'.join(
                            final_similar_words[m] for m in range(0, n_similar_words)
                        )

            string += '")'

            if counter < n_words_per_topic:
                string += " AND "
            else:
                string += ""

        string += ")"

        if topic_index < len(topics_list) - 1:
            string += " OR "
        else:
            string += ""

    return string


def generate_search_string(
    *,
    list_of_topics: List[List[str]],
    n_words_per_topic: int,
    n_similar_words: int,
    enrichment_text: str,
    bert_tokenizer: Any,
    bert_model: Any,
) -> str:
    """Generates a search string.

    Args:
        list_of_topics (List[List[str]]): List of topics, where each topic is a list of words.
        n_words_per_topic (int): Indicates how many words of each topic will be inserted into the string.
        n_similar_words (int): Number of similar words to generate for each word in each topic.
        enrichment_text (str): The text to use to enrich each word.
        bert_tokenizer: A BERT tokenizer.
        bert_model: A BERT model.

    Returns:
        A search string.

    Examples:
        >>> bert_tokenizer: Any = BertTokenizer.from_pretrained("bert-base-uncased")  # doctest: +SKIP
        >>> bert_model: Any = BertForMaskedLM.from_pretrained("bert-base-uncased")  # doctest: +SKIP
        >>> studies: list[EnrichmentStudy] = []
        >>> enrichment_text = generate_enrichment_text(studies_list=studies)  # doctest: +SKIP
        >>> generate_search_string(  # doctest: +SKIP
        ...     list_of_topics=[["topic1 word1", "topic1 word2"], ["topic2 word1", "topic2 word2"]],
        ...     number_of_words_per_topic=2,
        ...     number_of_similar_words=1,
        ...     enrichment_text=enrichment_text,
        ...     bert_tokenizer=bert_tokenizer,
        ...     bert_model=bert_model,
        ... )
        '(("code" OR "behavior") AND ("cloning")) OR (("smells" OR "classes") AND ("code" OR "behavior"))'
    """  # noqa: E501
    if n_similar_words == 0:
        return _generate_search_string_without_similar_words(
            topics_list=list_of_topics,
            n_words_per_topic=n_words_per_topic,
        )

    return _generate_search_string_with_similar_words(
        topics_list=list_of_topics,
        n_words_per_topic=n_words_per_topic,
        enrichment_text=enrichment_text,
        n_similar_words=n_similar_words,
        bert_tokenizer=bert_tokenizer,
        bert_model=bert_model,
    )


def set_pub_year(
    *,
    string: str,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
) -> str:
    """Given a search string, will append `PUBYEAR >` and `PUBYEAR <` boundaries as needed.

    Args:
        string (str): A search string.
        min_year (Optional[int], optional): Minimum year of publication. Defaults to None.
        max_year (Optional[int], optional): Maximum year of publication. Defaults to None.

    Returns:
        A search string with PUBYEAR boundaries.

    Examples:
        >>> set_pub_year(string='title("machine" and "learning")', max_year=2018)
        'title("machine" and "learning") AND PUBYEAR < 2018'
    """  # noqa: E501
    if min_year is not None:
        string += f" AND PUBYEAR > {min_year}"

    if max_year is not None:
        string += f" AND PUBYEAR < {max_year}"

    return string
