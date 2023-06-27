"""Enum defining the available topic extraction strategies.

This was put to a separate file to allow direct import.
"""

from enum import Enum


class TopicExtractionStrategy(str, Enum):
    """Enum defining the available topic extraction strategies.

    Examples:
        >>> lda_strategy = TopicExtractionStrategy.lda
        >>> lda_strategy.value
        'lda'
    """

    lda = "lda"
    bertopic = "bertopic"
