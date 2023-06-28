"""SeSG (Search String Generator) module."""
from importlib.metadata import version

from . import (
    evaluation,
    scopus,
    search_string,
    similar_words,
    snowballing,
    topic_extraction,
)


__all__ = [
    "evaluation",
    "scopus",
    "search_string",
    "snowballing",
    "topic_extraction",
    "similar_words",
]


__version__ = version(__name__)
