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
)
from .multi_client import MultiClientScopusSearchAbstractClass, create_clients_list


__all__ = (
    "APIKeyExpiredResponse",
    "BadRequestError",
    "ExceededTimeoutRetriesError",
    "OutOfAPIKeysError",
    "PayloadTooLargeError",
    "ScopusClient",
    "SuccessResponse",
    "TimeoutResponse",
    "MultiClientScopusSearchAbstractClass",
    "create_clients_list",
)
