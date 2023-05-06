"""Similar words module.

This module provides a way of generating similar words, and filtering them to return only the relevant ones.

!!!note
    It is worth noting that **similarity** in this context means contextual similarity (which is why we use BERT),
    and not string equality.
"""  # noqa: E501


from nltk.stem import LancasterStemmer
from rapidfuzz.distance import Levenshtein


_lancaster = LancasterStemmer()


def _strings_are_distant(
    s1: str,
    s2: str,
) -> bool:
    """Checks if the given strings have at least 5 units of levenshtein distance.

    Args:
        s1 (str): First string.
        s2 (str): Second string.

    Returns:
        True if the strings have at least 4 units of levenshtein distance, False otherwise.

    Examples:
        >>> _strings_are_distant("string", "string12345")
        True
        >>> _strings_are_distant("string", "strng")
        False
    """  # noqa: E501
    levenshtein_distance = 4
    return Levenshtein.distance(str(s1), str(s2)) > levenshtein_distance


def _strings_are_close(
    s1: str,
    s2: str,
) -> bool:
    """Checks if the given strings have at most 3 units of levenshtein distance.

    Args:
        s1 (str): First string.
        s2 (str): Second string.

    Returns:
        True if the strings have at most 3 units of levenshtein distance, False otherwise.

    Examples:
        >>> _strings_are_close("string", "big string")
        False
        >>> _strings_are_close("string", "strng")
        True
    """  # noqa: E501
    levenshtein_distance = 4
    return Levenshtein.distance(str(s1), str(s2)) < levenshtein_distance


def _stemmed_similar_word_is_valid(
    *,
    stemmed_similar_word: str,
    stemmed_word: str,
) -> bool:
    """Checks if the stemmed similar word is valid.

    A stemmed similar word is considered valid if it is not equal to the stemmed word, and if it is distant from the stemmed word.

    Args:
        stemmed_similar_word (str): The stemmed similar word.
        stemmed_word (str): The word itself.

    Returns:
        True if the strings are not equal and distant, False otherwise.
    """  # noqa: E501
    not_equal = stemmed_word != stemmed_similar_word
    distant = _strings_are_distant(stemmed_similar_word, stemmed_word)

    return not_equal and distant


def _stemmed_similar_word_is_duplicate(
    *,
    stemmed_similar_word: str,
    stemmed_similar_words_list: list[str],
) -> bool:
    """Checks if the stemmed similar word is a duplicate.

    A stemmed similar word is considered duplicate if it is close to one of the stemmed similar word in the list.

    Args:
        stemmed_similar_word (str): The stemmed similar word.
        stemmed_similar_words_list (list[str]): List of stemmed words to check against.

    Returns:
        True if the stemmed similar word is a duplicate, False otherwise.
    """  # noqa: E501
    for word in stemmed_similar_words_list:
        is_close = _strings_are_close(word, stemmed_similar_word)
        if is_close:
            return True

    return False


def get_bert_similar_words(
    word: str,
    *,
    enrichment_text: str,
    bert_tokenizer,
    bert_model,
) -> list[str] | None:
    """Tries to find words that are similar to the target word using the enrichment text.

    Args:
        word (str): Token to which other similar ones will be generated.
        enrichment_text (str): Text that will be used to find similar words.
        bert_tokenizer (Any): A BERT tokenizer.
        bert_model (Any): A BERT model.

    Returns:
        List of similar words. If the token has more than 1 word, of if it is no present in the enrichment text,
        will return None.
    """  # noqa: E501
    import numpy as np
    import torch

    if " " in word:
        return None

    selected_sentences: list[str] = []

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


def get_relevant_similar_words(
    word: str,
    *,
    bert_similar_words_list: list[str],
) -> list[str]:
    """Filters out similar words that are not relevant.

    Args:
        word (str): The word that was used to generate the similar ones.
        bert_similar_words_list (list[str]): List with the similar words found by BERT.

    Returns:
        List of words that are not close to each other.
    """
    stemmed_word: str = _lancaster.stem(word)
    stemmed_similar_words_list: list[str] = [
        _lancaster.stem(w) for w in bert_similar_words_list
    ]

    relevant_similar_words: list[str] = list()
    stemmed_relevant_similar_words: list[str] = list()

    zipped = zip(stemmed_similar_words_list, bert_similar_words_list)

    for stemmed_similar_word, similar_word in zipped:
        is_valid = _stemmed_similar_word_is_valid(
            stemmed_similar_word=stemmed_similar_word,
            stemmed_word=stemmed_word,
        )

        if not is_valid:
            continue

        is_duplicate = _stemmed_similar_word_is_duplicate(
            stemmed_similar_word=stemmed_similar_word,
            stemmed_similar_words_list=stemmed_relevant_similar_words,
        )

        if is_duplicate:
            continue

        relevant_similar_words.append(similar_word)
        stemmed_relevant_similar_words.append(stemmed_similar_word)

    return relevant_similar_words
