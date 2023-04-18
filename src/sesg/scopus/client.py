"""
Scopus Client module.

This module is responsible to provide an efficient, and error proof client for the Scopus API.
The client is optimized to scrape the maximum number of pages that are available from Scopus API,
which is 5000, for normal users, at the maximum speed possible.

We use [`aiometer`](https://github.com/florimondmanca/aiometer),
and [`httpx`](https://github.com/projectdiscovery/httpx) to achieve this goal.
"""  # noqa: E501

from typing import AsyncIterator, List, Union

from . import api


class OutOfAPIKeysError(Exception):
    """Used all API keys available."""


class ExceededTimeoutRetries(Exception):
    """Exceeded the number of timeout retries in a row."""


class APIKeyExpiredResponse:
    """Represents an API key expired response from the [`ScopusClient`][sesg.scopus.client.ScopusClient]"""  # noqa: E501


class TimeoutResponse:
    """Represents a timed out response from the [`ScopusClient`][sesg.scopus.client.ScopusClient]"""  # noqa: E501


class ScopusClient:
    """A Scopus API Client with automatic retry on timeout, and automatic
    API key swapping on expiry.

    Args:
        timeout (float): Time in seconds to wait before assuming the request timed out.
        timeout_retries (int): Number of times to retry a timed out request in a row.
        api_keys (List[str]): List with Scopus API keys.
    """

    __timeout: float
    __api_keys: List[str]
    __timeout_retries: int

    __current_api_key_index: int
    __current_timeout_retry: int
    __current_page: int
    __current_query: str

    def __init__(
        self,
        *,
        api_keys: List[str],
        timeout: float,
        timeout_retries: int,
    ) -> None:
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
        """Current page being fetched."""
        return self.__current_page

    @property
    def current_query(self) -> str:
        """Current query being searched."""
        return self.__current_query

    @property
    def api_keys(self) -> List[str]:
        """The Scopus API keys for this client."""
        return self.__api_keys

    def __restart_iterator_with_current_state(self):
        return api.search(
            api_key=self.current_api_key,
            query=self.__current_query,
            timeout=self.__timeout,
            page=self.__current_page,
        )

    async def __anext__(self):
        try:
            data = await self.__iterator.__anext__()

            self.__current_page += 1
            self.__current_timeout_retry = 0

            return data

        except api.PayloadTooLargeError as e:
            raise e

        except api.APIKeyExpiredError:
            self.__current_timeout_retry = 0
            self.__iterator = self.__restart_iterator_with_current_state()
            self.__current_api_key_index += 1

            if self.__current_api_key_index == len(self.__api_keys):
                raise OutOfAPIKeysError()

            return APIKeyExpiredResponse()

        except api.TimeoutError:
            if self.__current_timeout_retry == self.__timeout_retries - 1:
                raise ExceededTimeoutRetries()

            self.__current_timeout_retry += 1
            self.__iterator = self.__restart_iterator_with_current_state()

            return TimeoutResponse()

    def __aiter__(self):
        self.__current_page = 0
        self.__current_timeout_retry = 0
        self.__iterator = self.__restart_iterator_with_current_state()

        return self

    def search(
        self,
        query: str,
    ) -> AsyncIterator[
        Union[
            api.SuccessResponse,
            APIKeyExpiredResponse,
            TimeoutResponse,
        ]
    ]:
        """Performs Scopus API requests in a timeout-proof, and API key expiry-prof manner.

        Args:
            query (str): The query to search for.

        Returns:
            An AsyncIterator that yields one of the below:

                - A succesfull response
                - An API key expired response
                - A Timed out response

        Examples:
            >>> client = ScopusClient(api_keys=[], timeout=7, timeout_retries=10)
            >>> async for data in client.search("machie"):
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


async def m():
    client = ScopusClient(api_keys=[], timeout=7, timeout_retries=10)

    async for data in client.search("machie"):
        if isinstance(data, TimeoutResponse):
            print(f"Timed out on page {client.current_page}")

        elif isinstance(data, APIKeyExpiredResponse):
            print(
                f"API Key {client.current_api_key_index + 1} of {len(client.api_keys)} is expired."  # noqa: E501
            )
        else:
            # here data is of type [`SuccessResponse`][sesg.scopus.api.SuccessResponse]
            print(data.entries)
