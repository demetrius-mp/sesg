"""Similar words module.

This module provides a way of generating similar words, and filtering them to return only the relevant ones.

!!!note
    It is worth noting that **similarity** in this context means contextual similarity (which is why we use BERT),
    and not string equality.
"""  # noqa: E501


from dataclasses import dataclass
from string import punctuation
from typing import Iterator, Optional, Protocol

from nltk.stem import LancasterStemmer
from rapidfuzz.distance import Levenshtein


PUNCTUATION: set[str] = set(punctuation)


_lancaster = LancasterStemmer()


def _check_strings_are_distant(
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
        >>> _check_strings_are_distant("string", "string12345")
        True
        >>> _check_strings_are_distant("string", "strng")
        False
    """  # noqa: E501
    levenshtein_distance = 4
    return Levenshtein.distance(str(s1), str(s2)) > levenshtein_distance


def _check_strings_are_close(
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
        >>> _check_strings_are_close("string", "big string")
        False
        >>> _check_strings_are_close("string", "strng")
        True
    """  # noqa: E501
    levenshtein_distance = 4
    return Levenshtein.distance(str(s1), str(s2)) < levenshtein_distance


def _check_stemmed_similar_word_is_valid(
    stemmed_similar_word: str,
    *,
    stemmed_word: str,
) -> bool:
    """Checks if the stemmed similar word is valid.

    A stemmed similar word is considered valid if it complies the following criteria:

    - It is not equal to the stemmed word
    - It is distant from the stemmed word (see [_check_strings_are_distant][sesg.search_string.similar_words._check_strings_are_distant]).

    Args:
        stemmed_similar_word (str): The stemmed similar word.
        stemmed_word (str): The word itself.

    Returns:
        True if the strings are not equal and distant, False otherwise.

    Examples:
        >>> _check_stemmed_similar_word_is_valid(
        ...     "string",
        ...     stemmed_word="string"
        ... )
        False
        >>> _check_stemmed_similar_word_is_valid(
        ...     "string",
        ...     stemmed_word="stringified"
        ... )
        True
    """  # noqa: E501
    not_equal = stemmed_word != stemmed_similar_word
    distant = _check_strings_are_distant(stemmed_similar_word, stemmed_word)

    return not_equal and distant


def _check_stemmed_similar_word_is_duplicate(
    stemmed_similar_word: str,
    *,
    stemmed_similar_words_list: list[str],
) -> bool:
    """Checks if the stemmed similar word is a duplicate.

    A stemmed similar word is considered duplicate if it is close to one of the stemmed similar word in the list.

    Args:
        stemmed_similar_word (str): The stemmed similar word.
        stemmed_similar_words_list (list[str]): List of stemmed words to check against.

    Returns:
        True if the stemmed similar word is a duplicate, False otherwise.

    Examples:
        >>> _check_stemmed_similar_word_is_duplicate(
        ...     "string",
        ...     stemmed_similar_words_list=["other", "somewhat"],
        ... )
        False
        >>> _check_stemmed_similar_word_is_duplicate(
        ...     "string",
        ...     stemmed_similar_words_list=["strng", "something"],
        ... )
        True
    """  # noqa: E501
    for word in stemmed_similar_words_list:
        is_close = _check_strings_are_close(word, stemmed_similar_word)
        if is_close:
            return True

    return False


def _check_word_is_punctuation(
    word: str,
) -> bool:
    """Checks if the given word is not punctuation.

    This function uses `#!python string.punctuation` to get punctuation characters.

    Args:
        word (str): Word to check.

    Returns:
        True if the word is punctuation, False otherwise.

    Examples:
        >>> _check_word_is_punctuation("a")
        False
        >>> _check_word_is_punctuation(">")
        True
    """
    return word in PUNCTUATION


def _check_is_bert_oov_word(
    word: str,
) -> bool:
    """Checks if the given word is a BERT out-of-vocabulary (OOV) word.

    BERT represents OOV words as a string that starts with `##`.

    Args:
        word (str): Word to check.

    Returns:
        True if it is an OOV word, False otherwise.

    Examples:
        >>> _check_is_bert_oov_word("organization")
        False
        >>> _check_is_bert_oov_word("##ation")
        True
    """
    return word.startswith("##")


def _check_similar_word_is_relevant(
    similar_word: str,
    *,
    stemmed_word: str,
    stemmed_similar_word: str,
    stemmed_relevant_similar_words: list[str],
) -> bool:
    """Checks if the given similar word is relevant.

    A similar word is considered relevant if it complies the following criteria, in order:

    - It is not a BERT out-of-vocabulary word (see [_check_is_bert_oov_word][sesg.search_string.similar_words._check_is_bert_oov_word]).
    - It is not a punctuation character (see [_check_word_is_punctuation][sesg.search_string.similar_words._check_word_is_punctuation]).
    - It's stemmed form is valid (see [_stemmed_similar_word_is_valid][sesg.search_string.similar_words._stemmed_similar_word_is_valid]).
    - It's stemmed form is not a duplicate (see [_stemmed_similar_word_is_duplicate][sesg.search_string.similar_words._stemmed_similar_word_is_duplicate]).

    Args:
        similar_word (str): Similar word to check if is relevant.
        stemmed_word (str): Stemmed form of the original word.
        stemmed_similar_word (str): Stemmed form of the similar word.
        stemmed_relevant_similar_words (list[str]): List of stemmed relevant similar words to check for duplicate.

    Returns:
        True if the similar word is relevant, False otherwise.
    """  # noqa: E501
    is_bert_oov_word = _check_is_bert_oov_word(similar_word)
    if is_bert_oov_word:
        return False

    is_punctuation = _check_word_is_punctuation(similar_word)
    if is_punctuation:
        return False

    is_valid = _check_stemmed_similar_word_is_valid(
        stemmed_similar_word,
        stemmed_word=stemmed_word,
    )
    if not is_valid:
        return False

    is_duplicate = _check_stemmed_similar_word_is_duplicate(
        stemmed_similar_word,
        stemmed_similar_words_list=stemmed_relevant_similar_words,
    )
    if is_duplicate:
        return False

    return True


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
        List of similar words. If the token has more than 1 word, or if it is no present in the enrichment text, will return None.
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

    # Get top thirty possibilities for the masked word.
    predicted_index = torch.topk(predictions[0, masked_index], 30)[1]
    predicted_index = list(np.array(predicted_index))

    # ???????????????????????????????????????
    # ???????????????????????????????????????
    # ???????????????????????????????????????
    #
    # Remove the \2022 ascii error index.
    # for index in predicted_index:
    #     # doesn't make sense, since predicted_index has type `list[int]`
    #     # or does it make sense?
    #     if index == "1528":
    #         predicted_index.remove("1528")

    # for index in predicted_index:
    #     # what is wrong with token id 1000?
    #     # hard to track since the token may vary accordingly to the
    #     # `enrichment_text` and `word` params
    #     if index == 1000:
    #         predicted_index.remove(1000)
    #
    # ???????????????????????????????????????
    # ???????????????????????????????????????
    # ???????????????????????????????????????

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

    relevant_similar_words: list[str] = list()
    stemmed_relevant_similar_words: list[str] = list()

    stemmed_similar_words_list: Iterator[str] = (
        _lancaster.stem(w) for w in bert_similar_words_list
    )
    zipped = zip(stemmed_similar_words_list, bert_similar_words_list)

    for stemmed_similar_word, similar_word in zipped:
        similar_word_is_relevant = _check_similar_word_is_relevant(
            similar_word,
            stemmed_word=stemmed_word,
            stemmed_similar_word=stemmed_similar_word,
            stemmed_relevant_similar_words=stemmed_relevant_similar_words,
        )

        if not similar_word_is_relevant:
            continue

        relevant_similar_words.append(similar_word)
        stemmed_relevant_similar_words.append(stemmed_similar_word)

    return relevant_similar_words


class SimilarWordsFinderCacheProtocol(Protocol):
    """Interface for the cache system used in [SimilarWordsFinder][sesg.search_string.similar_words.SimilarWordsFinder].

    Examples:
        >>> class DictCache(SimilarWordsFinderCacheProtocol):
        ...     def __init__(self):
        ...         self.cache: dict[str, list[str]] = dict()
        ...
        ...     def get(self, key: str) -> list[str] | None:
        ...         return self.cache.get(key)
        ...
        ...     def set(self, key: str, value: list[str]):
        ...         self.cache[key] = value
        ...
        >>> cache = DictCache()
        >>> cache.set("key", ["value"])
        >>> cache.get("key")
        ['value']
        >>> cache.get("other key") is None
        True

    """  # noqa: E501

    def get(  # pragma: no cover
        self,
        key: str,
    ) -> list[str] | None:
        """Gets a value from the cache.

        Args:
            key (str): Key to retrieve.

        Returns:
            The value associated with the key, if it exists, None otherwise.
        """
        raise NotImplementedError("Not implemented")  # pragma: no cover

    def set(  # pragma: no cover
        self,
        key: str,
        value: list[str],
    ) -> None:
        """Sets a value in the cache.

        Args:
            key (str): Key to set.
            value (list[str]): Value to associate with the key.
        """
        raise NotImplementedError("Not implemented")  # pragma: no cover


@dataclass
class SimilarWordsFinder:
    """Composes [get_bert_similar_words][sesg.search_string.similar_words.get_bert_similar_words] and [get_relevant_similar_words][sesg.search_string.similar_words.get_relevant_similar_words].

    Returns a callable that will check the cache before computing the similar words.
    """  # noqa: E501

    enrichment_text: str
    bert_tokenizer: ...
    bert_model: ...
    cache: Optional[SimilarWordsFinderCacheProtocol] = None

    def __call__(
        self,
        word: str,
    ) -> list[str]:
        """Finds the similar words of the word passed as argument, using the cache if available.

        Args:
            word (str): The word to which look for similar ones.

        Returns:
            List of strings with the similar words. Notice that the word itself is included in the final list (as the first element).
        """  # noqa: E501
        if self.cache is not None and (value := self.cache.get(word)) is not None:
            return value

        similar_words_list = [word]

        bert_similar_words = get_bert_similar_words(
            word,
            enrichment_text=self.enrichment_text,
            bert_model=self.bert_model,
            bert_tokenizer=self.bert_tokenizer,
        )

        if bert_similar_words is not None:
            relevant_similar_words = get_relevant_similar_words(
                word,
                bert_similar_words_list=bert_similar_words,
            )

            similar_words_list.extend(relevant_similar_words)

        if self.cache is not None:
            self.cache.set(word, similar_words_list)

        return similar_words_list
