"""Snowballing module.

Snowballing strategies to retrieve the citation graph of a set of studies.
"""

from .fuzzy_bsb import FuzzyBackwardSnowballingStudy, fuzzy_backward_snowballing


__all__ = (
    "fuzzy_backward_snowballing",
    "FuzzyBackwardSnowballingStudy",
)
