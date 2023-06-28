"""Generate similar words using BERT."""

from dataclasses import dataclass
from typing import Any, TypedDict

import numpy as np
import torch

from .protocol import SimilarWordsGenerator


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


@dataclass
class BertSimilarWordsGenerator(SimilarWordsGenerator):
    """Generate similar words using BERT.

    Attributes:
        enrichment_text (str): Text that will be used to find similar words.
        bert_tokenizer (Any): A BERT tokenizer. For example, `BertTokenizer.from_pretrained("bert-base-uncased")`.
        bert_model (Any): A BERT model. For example, `BertForMaskedLM.from_pretrained("bert-base-uncased")`.
    """  # noqa: E501

    @staticmethod
    def create_enrichment_text(
        studies_list: list[EnrichmentStudy],
    ) -> str:
        r"""Creates a piece of text that consists of the concatenation of the title and abstract of each study.

        Args:
            studies_list (list[EnrichmentStudy]): List of studies with title and abstract.

        Returns:
            The enrichment text.

        Examples:
            >>> studies = [
            ...     EnrichmentStudy(title="title1", abstract="abstract1"),
            ...     EnrichmentStudy(title="title2", abstract="abstract2 \r\ntext"),
            ...     EnrichmentStudy(title="title3", abstract="abstract3"),
            ... ]
            >>> BertSimilarWordsGenerator.create_enrichment_text(studies_list=studies)
            'title1 abstract1\ntitle2 abstract2 #.text\ntitle3 abstract3\n'
        """  # noqa: E501
        enrichment_text = ""
        for study in studies_list:
            title = study["title"]
            abstract = study["abstract"]

            line = f"{title} {abstract}".strip().replace("\r\n", "#.") + "\n"
            enrichment_text += line

        return enrichment_text

    enrichment_text: str
    bert_tokenizer: Any
    bert_model: Any

    def __call__(self, word: str) -> list[str]:
        """Generate similar words using BERT.

        Args:
            word (str): Word from which to find similar words.

        Returns:
            List of similar words.
        """
        if " " in word:
            return []

        selected_sentences: list[str] = []

        # Treatment for if the selected sentence is the last sentence of the text (return only one sentence).  # noqa: E501
        for sentence in self.enrichment_text.split("."):
            if word in sentence or word in sentence.lower():
                selected_sentences.append(sentence + ".")
                break

        formated_sentences = "[CLS] "
        for sentence in selected_sentences:
            formated_sentences += sentence.lower() + " [SEP] "

        tokenized_text = self.bert_tokenizer.tokenize(formated_sentences)

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
        indexed_tokens = self.bert_tokenizer.convert_tokens_to_ids(tokenized_text)

        # Define sentence A and B indices associated to first and second sentences.
        len_first = tokenized_text.index("[SEP]")
        len_first = len_first + 1
        segments_ids = [0] * len_first + [1] * (len(tokenized_text) - len_first)

        # Convert the inputs to PyTorch tensors.
        tokens_tensor = torch.tensor([indexed_tokens])
        segments_tensors = torch.tensor([segments_ids])

        # Predict all tokens.
        with torch.no_grad():
            outputs = self.bert_model(tokens_tensor, token_type_ids=segments_tensors)
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

        predicted_tokens: list[str] = self.bert_tokenizer.convert_ids_to_tokens(
            predicted_index
        )

        return [
            token for token in predicted_tokens if not check_is_bert_oov_word(token)
        ]
