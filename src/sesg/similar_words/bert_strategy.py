"""Generate similar words using BERT."""


def check_is_bert_oov_word(
    word: str,
) -> bool:
    """Checks if the given word is a BERT out-of-vocabulary (OOV) word.

    BERT represents OOV words as a string that starts with `##`.

    Args:
        word (str): Word to check.

    Returns:
        True if it is an OOV word, False otherwise.

    Examples:
        >>> check_is_bert_oov_word("organization")
        False
        >>> check_is_bert_oov_word("##ation")
        True
    """
    return word.startswith("##")


def get_similar_words_with_bert(
    word: str,
    *,
    enrichment_text: str,
    bert_tokenizer,
    bert_model,
) -> list[str]:
    """Tries to find words that are similar to the target word using the enrichment text.

    Args:
        word (str): Token to which other similar ones will be generated.
        enrichment_text (str): Text that will be used to find similar words.
        bert_tokenizer (Any): A BERT tokenizer. For example, `BertTokenizer.from_pretrained("bert-base-uncased")`.
        bert_model (Any): A BERT model. For example, `BertForMaskedLM.from_pretrained("bert-base-uncased")`.

    Returns:
        List of similar words. If the token has more than 1 word, or if it is not present in the enrichment text, will return None.
    """  # noqa: E501
    import numpy as np
    import torch

    if " " in word:
        return []

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
        return []

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
    # # Remove the \2022 ascii error index.
    # for index in predicted_index:
    #     # doesn't make sense, since predicted_index has type `list[int]`
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

    predicted_tokens: list[str] = bert_tokenizer.convert_ids_to_tokens(predicted_index)

    return [token for token in predicted_tokens if not check_is_bert_oov_word(token)]
