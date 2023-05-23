"""Scopus Client module.

This module is responsible to provide an efficient, and error proof client for the Scopus API.
The client is optimized to scrape the maximum number of pages that are available from Scopus API,
which is 5000, for normal users, at the maximum speed possible.

We use [`aiometer`](https://github.com/florimondmanca/aiometer),
and [`httpx`](https://github.com/projectdiscovery/httpx) to achieve this goal.
"""  # noqa: E501

from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator, Optional

from . import api


class OutOfAPIKeysError(Exception):
    """Used all API keys available."""


class ExceededTimeoutRetriesError(Exception):
    """Exceeded the number of timeout retries in a row."""


@dataclass
class APIKeyExpiredResponse:
    """Represents an API key expired response from the [`ScopusClient`][sesg.scopus.client.ScopusClient].

    Args:
        api_key (str): The expired API key.
        api_key_index (int): The index of the expired API key on the list of API keys passed to [`ScopusClient`][sesg.scopus.client.ScopusClient].
        resets_at (Optional[datetime]): Datetime object represents when the API key will be resetted.
    """  # noqa: E501

    api_key: str
    api_key_index: int
    resets_at: Optional[datetime]


@dataclass
class TimeoutResponse:
    """Represents a timed out response from the [`ScopusClient`][sesg.scopus.client.ScopusClient].

    Args:
        timed_out_page (int): The page where the timeout occured.
        timeout_retry (int): The current timeout retry attempt for a same request.
    """  # noqa: E501

    timed_out_page: int
    timeout_retry: int


class ScopusClient:
    """A Scopus API Client with automatic retry on timeout, and automatic API key swapping on expiry."""  # noqa: E501

    __timeout: float
    __api_keys: list[str]
    __timeout_retries: int

    __current_api_key_index: int
    __current_timeout_retry: int
    __current_page: int
    __current_query: str

    def __init__(
        self,
        *,
        api_keys: list[str],
        timeout: float,
        timeout_retries: int,
    ) -> None:
        """Creates a ScopusClient.

        Args:
            api_keys (list[str]): List with Scopus API keys.
            timeout (float): Time in seconds to wait before assuming the request timed out.
            timeout_retries (int): Number of times to retry a timed out request in a row.
        """  # noqa: E501
        self.__timeout = timeout
        self.__api_keys = api_keys
        self.__timeout_retries = timeout_retries

        self.__current_api_key_index = 0
        self.__current_timeout_retry = 0
        self.__current_page = 0

    @property
    def current_api_key(self) -> str:
        """Current API key being used."""
        return self.__api_keys[self.__current_api_key_index]

    @property
    def current_api_key_index(self) -> int:
        """Index on the list of the current API key being used."""
        return self.__current_api_key_index

    @property
    def current_page(self) -> int:
        """Current page being fetched.

        Starts at 1, being at most 200.
        """
        return self.__current_page

    @property
    def current_query(self) -> str:
        """Current query being used."""
        return self.__current_query

    @property
    def api_keys(self) -> list[str]:
        """The Scopus API keys for this client."""
        return self.__api_keys

    @property
    def current_timeout_retry(self) -> int:
        """The current retry for the same timed out request."""
        return self.__current_timeout_retry

    @property
    def timeout(self) -> float:
        """The `timeout` parameter."""
        return self.__timeout

    @property
    def timeout_retries(self) -> float:
        """The `timeout_retries` parameter."""
        return self.__timeout_retries

    def __restart_iterator_with_current_state(self):
        return api.search(
            api_key=self.current_api_key,
            query=self.__current_query,
            timeout=self.__timeout,
            page=self.__current_page,
        )

    async def __anext__(
        self,
    ) -> api.SuccessResponse | APIKeyExpiredResponse | TimeoutResponse:
        """Returns the next result of the search iterator.

        Raises:
            ExceededTimeoutRetriesError: If exceeds the number of timeout retries in a row.
            OutOfAPIKeysError: If used al API keys available.
            PayloadTooLargeError: If the response status code is 413. Probably indicates that the search string is too large.
            BadRequestError: If the response status code is 400. Probably indicates that the search string is malformed.

        Returns:
            One of the below:

                - A succesfull response
                - An API key expired response
                - A Timed out response
        """  # noqa: E501
        try:
            response = await self.__iterator.__anext__()

            self.__current_page += 1
            self.__current_timeout_retry = 0

            return response

        except (api.PayloadTooLargeError, api.BadRequestError) as e:
            raise e

        except api.APIKeyExpiredError as e:
            response = APIKeyExpiredResponse(
                api_key=self.current_api_key,
                api_key_index=self.current_api_key_index,
                resets_at=e.resets_at,
            )

            if self.__current_api_key_index + 1 == len(self.__api_keys):
                raise OutOfAPIKeysError()

            self.__current_timeout_retry = 0
            self.__current_api_key_index += 1
            self.__iterator = self.__restart_iterator_with_current_state()

            return response

        except api.TimeoutError:
            if self.__current_timeout_retry == self.__timeout_retries - 1:
                raise ExceededTimeoutRetriesError()

            response = TimeoutResponse(
                timed_out_page=self.current_page,
                timeout_retry=self.current_timeout_retry,
            )

            self.__current_timeout_retry += 1
            self.__iterator = self.__restart_iterator_with_current_state()

            return response

    def __aiter__(self):
        """Returns an async iterator over the results of the current query."""
        self.__current_page = 0
        self.__current_timeout_retry = 0
        self.__iterator = self.__restart_iterator_with_current_state()

        return self

    def search(
        self,
        query: str,
    ) -> AsyncIterator[api.SuccessResponse | APIKeyExpiredResponse | TimeoutResponse]:
        """Performs Scopus API requests in a timeout-proof, and API key expiry-prof manner.

        !!! note

            Notice that the exceptions on the **Raises**
            section occurs during iteration time, not at function call time.

        Args:
            query (str): The query to search for.

        Raises:
            ExceededTimeoutRetriesError: If exceeds the number of timeout retries in a row.
            OutOfAPIKeysError: If used al API keys available.
            PayloadTooLargeError: If the response status code is 413. Probably indicates that the search string is too large.
            BadRequestError: If the response status code is 400. Probably indicates that the search string is malformed.

        Returns:
            An AsyncIterator that yields one of the below:

                - A succesfull response
                - An API key expired response
                - A Timed out response

        Examples:
            >>> client = ScopusClient(api_keys=[], timeout=7, timeout_retries=10)
            >>> async for data in client.search("machine"):  # doctest: +SKIP
            ...     if isinstance(data, TimeoutResponse):
            ...         print(f"Timed out on page {client.current_page}")
            ...
            ...     elif isinstance(data, APIKeyExpiredResponse):
            ...         print(f"API Key {client.current_api_key_index + 1} of {len(client.api_keys)} is expired.")
            ...
            ...     else:
            ...         # here data is of type `SuccessResponse`
            ...         print(data.entries)
        """  # noqa: E501
        self.__current_query = query

        return self.__aiter__()
