"""Similar words module.

Provides strategies for extracting similar words from a given word
and filtering them.
"""

from .bert_strategy import BertSimilarWordsGenerator
from .protocol import SimilarWordsGenerator
from .stemming_filter import filter_with_stemming


__all__ = (
    "filter_with_stemming",
    "BertSimilarWordsGenerator",
    "SimilarWordsGenerator",
)
