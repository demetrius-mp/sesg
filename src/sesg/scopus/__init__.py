"""Scopus module.

This module is responsible to communicate with Scopus API, providing an
efficient client that can fetch as much data as it can, as fast as
possible.
"""

from .api import (
    BadRequestError,
    PayloadTooLargeError,
    SuccessResponse,
)
from .client import (
    APIKeyExpiredResponse,
    ExceededTimeoutRetriesError,
    OutOfAPIKeysError,
    ScopusClient,
    TimeoutResponse,
    create_clients_with_disjoint_api_keys,
)


__all__ = (
    "APIKeyExpiredResponse",
    "BadRequestError",
    "ExceededTimeoutRetriesError",
    "OutOfAPIKeysError",
    "PayloadTooLargeError",
    "ScopusClient",
    "SuccessResponse",
    "TimeoutResponse",
    "create_clients_with_disjoint_api_keys",
)
