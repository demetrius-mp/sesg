import asyncio
import math
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from json import JSONDecodeError
from typing import (
    AsyncIterator,
    List,
    Optional,
    Union,
)

import aiometer
import httpx


@dataclass
class _ScopusSearchResults:
    """Represents a response obtained from the Scopus Search API.

    Args:
        total_results (int): Total number of results that were found by Scopus.
        Notice that Scopus will return at most 5_000, even if it has found more than 5_000.
        entries (List[Entry]): List of studies returned by the API.
    """  # noqa: E501

    @dataclass
    class Entry:
        """Represents a study entry.

        Args:
            title (str): Title of the study
        """  # noqa: E501

        title: str

    total_results: int
    entries: List[Entry]


class _ScopusPayloadTooLargeException(Exception):
    """The search string is too large."""

    ...


class _ScopusTimeoutException(Exception):
    """The request took too long to complete."""

    ...


class _ScopusAPIKeyExpiredException(Exception):
    """The API key used is expired (used over 20_000 times).

    Args:
        resets_at (Optional[datetime]): When the API key will be ready to use again. Defaults to None.
    """  # noqa: E501

    resets_at: Optional[datetime]

    def __init__(
        self,
        resets_at: Optional[datetime] = None,
    ) -> None:
        self.resets_at = resets_at


# base URL for Scopus API.
_SCOPUS_API_URL = "https://api.elsevier.com/content/search/scopus"


def _api_key_is_expired(
    res: httpx.Response,
) -> bool:
    """Checks if a Scopus API key is expired, given the response to a Scopus Request.

    Args:
        res (httpx.Response): A response object obtained from a Scopus Request.

    Returns:
        bool: True if the API key is expired, False otherwise.
    """  # noqa: E501
    remaining = res.headers.get("x-ratelimit-remaining")
    remaining_condition = remaining is not None and int(remaining) <= 0

    els_status_condition = (
        res.headers.get("x-els-status") == "QUOTA_EXCEEDED - Quota Exceeded"
    )
    return remaining_condition or els_status_condition


def _get_api_key_reset_date(
    res: httpx.Response,
) -> Union[None, datetime]:
    """Given a Scopus API response, will try do determine the reset date using the response headers.

    Args:
        res (httpx.Response): A Scopus API response.

    Returns:
        Union[None, datetime]: A datetime representing the reset date, or None if it wasn't able to determine it.
    """  # noqa: E501
    timestamp = res.headers.get("X-RateLimit-Reset")
    if timestamp is None:
        return None

    return datetime.fromtimestamp(int(timestamp))


async def _fetch_or_raise_scopus_exception(
    client: httpx.AsyncClient,
    timeout: float,
    req: httpx.Request,
) -> httpx.Response:
    """Fetches the given request, and if needed, raises a custom Exception.

    Args:
        client (httpx.AsyncClient): Async client that will fetch the request.
        timeout (int): How long to wait for the request to complete.
        req (httpx.Request): The request to fetch.

    Raises:
        _ScopusTimeoutException: If the request takes longer than the given `timeout`.
        _ScopusAPIKeyExpiredException: If the response has a header indicating that the
        API Key is expired.

    Returns:
        httpx.Response: A response ready to be used.
    """
    try:
        task = client.send(req)
        response = await asyncio.wait_for(
            fut=task,
            timeout=timeout,
        )

    except (asyncio.TimeoutError, httpx.ConnectError):
        raise _ScopusTimeoutException()

    if _api_key_is_expired(response):
        resets_at = _get_api_key_reset_date(response)
        raise _ScopusAPIKeyExpiredException(resets_at=resets_at)

    return response


def _create_scopus_search_request(
    api_key: str,
    query: str,
    start: Optional[int] = 0,
) -> httpx.Request:
    """Creates a `httpx.Request` for Scopus API.

    Args:
        api_key (str): A Scopus API key.
        query (str): Search string to use.
        start (int, optional): Start parameter, used for pagination. Defaults to 0.

    Returns:
        httpx.Request: A request object with the given information.
    """  # noqa: E501
    params = {
        "query": query,
        "apiKey": api_key,
        "start": start,
    }

    headers = {
        "Accept": "application/json",
    }

    request = httpx.Request(
        "GET",
        _SCOPUS_API_URL,
        params=params,
        headers=headers,
    )

    return request


def _parse_scopus_response(
    res: httpx.Response,
) -> _ScopusSearchResults:
    """Parses a Scopus API response.

    Args:
        res (httpx.Response): A Scopus API response.

    Returns:
        _ScopusSearchResults: An object with the information extracted from the json.
        Will filter out entries that do not have any title.
    """  # noqa: E501
    try:
        json = res.json()
    except JSONDecodeError:
        raise _ScopusPayloadTooLargeException()

    total_results = int(json["search-results"]["opensearch:totalResults"])

    entries = [
        _ScopusSearchResults.Entry(
            title=entry["dc:title"],
        )
        for entry in json["search-results"]["entry"]
        if "dc:title" in entry
    ]

    return _ScopusSearchResults(
        total_results=total_results,
        entries=entries,
    )


async def _scopus_search(
    api_key: str,
    query: str,
    timeout: float,
    page: int,
) -> AsyncIterator[_ScopusSearchResults]:
    """Performs Scopus API calls, in a manner that will return
    all available results, which is at most 5000.

    Args:
        api_key (str): Valid Scopus API key.
        query (str): Query to search for.
        timeout (int): How long to wait for the request to complete.
        page (int): Page where to start the search.

    Raises:
        _ScopusTimeoutException: If the request takes longer than the given `timeout`.
        _ScopusAPIKeyExpiredException: If the response indicates that the API Key is expired.

    Yields:
        AsyncIterator[_ScopusSearchResults]: Async iterator that yields each page found.
    """  # noqa: E501
    client = httpx.AsyncClient()

    first_request = _create_scopus_search_request(
        api_key=api_key,
        query=query,
        start=page * 25,
    )

    response = await _fetch_or_raise_scopus_exception(
        client=client,
        req=first_request,
        timeout=timeout,
    )

    results = _parse_scopus_response(response)

    yield results

    paginator = range((page + 1) * 25, min(5000, results.total_results), 25)
    requests = [
        _create_scopus_search_request(
            api_key=api_key,
            query=query,
            start=page_start,
        )
        for page_start in paginator
    ]

    async with aiometer.amap(
        partial(_fetch_or_raise_scopus_exception, client, timeout),
        requests,
        max_per_second=7,
        max_at_once=7,
    ) as results:
        async for response in results:
            results = _parse_scopus_response(response)

            yield results


class ScopusClient:
    """A Scopus API Client that redoes requests if it takes longer than a given timeout,
    and automatically rotates API keys once one of them expires.
    """  # noqa: E501

    __slots__ = (
        "__timeout",
        "__api_keys",
        "__timeout_attempts",
        "__ResultsIterator",
        "_private_current_api_key_index",
    )

    __timeout: float
    __api_keys: List[str]
    __timeout_attempts: int

    _private_current_api_key_index: int

    @dataclass
    class SearchResults(_ScopusSearchResults):
        current_page: int
        number_of_pages: int

    @dataclass
    class APIKeyExpiredError:
        api_key: str
        api_key_index: int
        resets_at: Union[datetime, None]

    @dataclass
    class APITimeoutError:
        current_attempt: int
        current_page: int

    def __init__(
        self,
        timeout: float,
        api_keys: List[str],
        timeout_attempts: int,
    ) -> None:
        self.__timeout = timeout
        self.__api_keys = api_keys
        self.__timeout_attempts = timeout_attempts
        self._private_current_api_key_index = 0

        class ResultsIterator:
            __slots__ = (
                "timeout",
                "api_keys",
                "query",
                "timeout_attempts",
                "scopus_client",
                "current_page",
                "iterator",
                "current_attempt",
            )

            timeout: float
            api_keys: List[str]
            query: str
            timeout_attempts: int
            scopus_client: ScopusClient

            iterator: AsyncIterator[_ScopusSearchResults]
            current_page: int
            current_attempt: int

            def __init__(
                self,
                scopus_client: ScopusClient,
                timeout: float,
                query: str,
                api_keys: List[str],
                timeout_attempts: int,
            ) -> None:
                self.timeout = timeout
                self.query = query
                self.api_keys = api_keys
                self.timeout_attempts = timeout_attempts
                self.scopus_client = scopus_client

                self.current_page = 0
                self.current_attempt = 0
                self.iterator = _scopus_search(
                    api_key=self.api_key,
                    query=self.query,
                    timeout=self.timeout,
                    page=self.current_page,
                )

            @property
            def api_key(self):
                if self.api_key_index == len(self.api_keys):
                    raise RuntimeError("All API keys are expired.")

                return self.api_keys[self.api_key_index]

            @property
            def api_key_index(self):
                return self.scopus_client._private_current_api_key_index

            @api_key_index.setter
            def api_key_index(self, value: int):
                self.scopus_client._private_current_api_key_index = value

            async def __anext__(self):
                try:
                    data = await self.iterator.__anext__()

                    number_of_pages = math.ceil(min(5000, data.total_results) / 25)
                    result = ScopusClient.SearchResults(
                        total_results=data.total_results,
                        current_page=self.current_page,
                        entries=data.entries,
                        number_of_pages=number_of_pages,
                    )

                    self.current_page += 1
                    self.current_attempt = 0

                    return result

                except _ScopusPayloadTooLargeException:
                    raise StopAsyncIteration()

                except _ScopusAPIKeyExpiredException as e:
                    error = ScopusClient.APIKeyExpiredError(
                        api_key=self.api_key,
                        api_key_index=self.api_key_index,
                        resets_at=e.resets_at,
                    )

                    self.current_attempt = 0
                    self.iterator = _scopus_search(
                        api_key=self.api_key,
                        query=self.query,
                        timeout=self.timeout,
                        page=self.current_page,
                    )
                    self.api_key_index += 1

                    return error

                except _ScopusTimeoutException as e:
                    if self.current_attempt == self.timeout_attempts - 1:
                        raise e

                    error = ScopusClient.APITimeoutError(
                        current_page=self.current_page,
                        current_attempt=self.current_attempt,
                    )

                    self.current_attempt += 1
                    self.iterator = _scopus_search(
                        api_key=self.api_key,
                        query=self.query,
                        timeout=self.timeout,
                        page=self.current_page,
                    )

                    return error

            def __aiter__(self):
                return self

        self.__ResultsIterator = ResultsIterator

    def search(
        self,
        query: str,
    ) -> AsyncIterator[
        Union[
            "ScopusClient.SearchResults",
            "ScopusClient.APIKeyExpiredError",
            "ScopusClient.APITimeoutError",
        ],
    ]:
        """Performs a search on Scopus API with the given query.
        Will automatically swap API keys when the current one expires.
        Also, if a request takes longer than `timeout` seconds,
        the request will be made again, up to `timeout_attempts` times in a row.

        Args:
            query (str): The query to search for.

        Returns:
            Async iterator that yields either A SearchResults instance, an APIKeyExpiredError instance, or an APITimeoutError instance.

        Examples:
            >>> async def use_client():
            ...     scopus_client = ScopusClient(
            ...         timeout=5,
            ...         api_keys=["key1", "key2", ...],
            ...         timeout_attempts=10,
            ...     )
            ...
            ...     async for data in scopus_client.search("machine learning"):
            ...         if isinstance(data, ScopusClient.SearchResults):
            ...             ...
            ...
            ...         if isinstance(data, ScopusClient.APIKeyExpiredError):
            ...             ...
            ...
            ...         if isinstance(data, ScopusClient.APITimeoutError):
            ...             ...
        """  # noqa: E501
        iterator = self.__ResultsIterator(
            scopus_client=self,
            timeout=self.__timeout,
            api_keys=self.__api_keys,
            timeout_attempts=self.__timeout_attempts,
            query=query,
        )

        return iterator.__aiter__()

    @dataclass
    class APIKeyHeaders:
        els_status: Optional[str]
        rate_limit_limit: Optional[int]
        rate_limit_remaining: Optional[int]
        rate_limit_reset: Optional[datetime]

    def get_api_key_headers(
        self,
        index: int,
    ) -> APIKeyHeaders:
        """Returns the response headers of a request made with the API key at the given index.

        Args:
            index (int): Index on the list of the API key that will be used.

        Returns:
            APIKeyHeaders: Object with the headers information.

        Examples:
            >>> async def use_client():
            ...     scopus_client = ScopusClient(
            ...         timeout=5,
            ...         api_keys=["key1", "key2", ...],
            ...         timeout_attempts=10,
            ...     )
            ...
            ...     scopus_client.get_api_key_headers(1)  # will use `key2`
        """  # noqa: E501
        res = httpx.get(
            _SCOPUS_API_URL,
            params={
                "apiKey": self.__api_keys[index],
                "query": "machine learning",
            },
        )

        els_status = res.headers.get("x-els-status")

        rate_limit_limit = res.headers.get("X-RateLimit-Limit")
        rate_limit_limit = int(rate_limit_limit) if rate_limit_limit else None

        rate_limit_remaining = res.headers.get("X-RateLimit-Remaining")
        rate_limit_remaining = (
            int(rate_limit_remaining) if rate_limit_remaining else None
        )

        rate_limit_reset = res.headers.get("X-RateLimit-Reset")
        rate_limit_reset = (
            datetime.fromtimestamp(int(rate_limit_reset)) if rate_limit_reset else None
        )

        return ScopusClient.APIKeyHeaders(
            els_status=els_status,
            rate_limit_limit=rate_limit_limit,
            rate_limit_remaining=rate_limit_remaining,
            rate_limit_reset=rate_limit_reset,
        )
