"""Search string module."""

from typing import Optional

from .generate import create_enrichment_text, generate_search_string
from .similar_words import SimilarWordsFinder, SimilarWordsFinderCacheProtocol


__all__ = (
    "create_enrichment_text",
    "generate_search_string",
    "SimilarWordsFinder",
    "SimilarWordsFinderCacheProtocol",
)


class InvalidPubyearBoundariesError(ValueError):
    """The provided pubyear boundaries are invalid."""


def set_pub_year_boundaries(
    string: str,
    *,
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
        >>> set_pub_year_boundaries(string='title("machine" and "learning")', max_year=2018)
        'title("machine" and "learning") AND PUBYEAR < 2018'
    """  # noqa: E501
    has_min_year = min_year is not None
    has_max_year = max_year is not None

    if has_min_year and has_max_year and min_year >= max_year:
        raise InvalidPubyearBoundariesError("Max year must be greater than min year")

    if has_min_year:
        string += f" AND PUBYEAR > {min_year}"

    if has_max_year:
        string += f" AND PUBYEAR < {max_year}"

    return string
