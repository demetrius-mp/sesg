"""Scopus module.

This module is responsible to communicate with Scopus API, providing an
efficient client that can fetch as much data as it can, as fast as
possible.
"""

from .client import OutOfAPIKeysError, ScopusClient, SuccessResponse


__all__ = [
    "ScopusClient",
    "OutOfAPIKeysError",
    "SuccessResponse",
]
