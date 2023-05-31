"""Evaluation module.

This module provides a method to evaluate the performance of a search string
generated with SeSG.
"""

from .evaluation_factory import EvaluationFactory, Study
from .graph import create_citation_graph


__all__ = [
    "EvaluationFactory",
    "create_citation_graph",
    "Study",
]
