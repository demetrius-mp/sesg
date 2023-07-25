"""This module provides a Scopus client that efficiently uses your API keys.

It is highly recommended to use [`trio`](https://trio.readthedocs.io/) to run async functions
as it was much faster on our tests.
"""  # noqa: E501

import math
from dataclasses import dataclass
from functools import partial
from json.decoder import JSONDecodeError
from ssl import SSLError
from typing import Any, AsyncIterable, NoReturn

import aiometer
import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt
from typing_extensions import TypedDict

from .mutable_cycle import MutableCycle


SCOPUS_API_URL = "https://api.elsevier.com/content/search/scopus"

# it is actually 9 (https://dev.elsevier.com/api_key_settings.html)
# but we are using 8 to be safe
MAX_REQUESTS_PER_SECOND_PER_API_KEY = 8

MAX_ATTEMPTS_ON_JSON_DECODE_ERROR = 5
MAX_ATTEMPTS_ON_KEY_ERROR = 5
MAX_ATTEMPTS_ON_SCOPUS_INTERNAL_ERROR = 5
MAX_ATTEMPTS_ON_SSL_ERROR = 5


@dataclass(frozen=True)
class Page:
    """A successfull Scopus Response.

    Args:
        n_results (int): Number of results for this query. Notice that even if it displays more than 5000 results, Scopus will limit to retrieve only 5000.
        n_pages (int): Number of pages that needs to be fetched to get all results. Limited to 200 due to Scopus API 5000 entries limit.
        current_page (int): Current page being fetched. Starts at 1, being at most 200.
        entries (list[Entry]): Studies returned from the API.
    """  # noqa: E501

    @dataclass
    class Entry:
        """A study entry returned from the API.

        Args:
            scopus_id (str): The ID of the study determined by Scopus.
            title (str): The title of the study.
            cited_by_count (Optional[int]): How many studies cites this one.
        """

        scopus_id: str
        title: str
        cited_by_count: int | None
        _rest: Any

    n_results: int
    n_pages: int
    current_page: int
    entries: list[Entry]


def parse_response(
    response: httpx.Response,
) -> Page:
    """Parses a Scopus API response.

    Args:
        response (httpx.Response): A Scopus API response.

    Returns:
        A [`Page`][sesg.scopus.client.Page] instance.
    """  # noqa: E501
    json = response.json()

    number_of_results = int(json["search-results"]["opensearch:totalResults"])
    start_index = int(json["search-results"]["opensearch:startIndex"])
    current_page = math.floor(start_index / 25) + 1
    number_of_pages = min(math.ceil(number_of_results / 25), 200)

    entries = [
        Page.Entry(
            title=entry["dc:title"],
            scopus_id=entry["dc:identifier"],
            cited_by_count=entry.get("citedby-count", None),
            _rest=entry,
        )
        for entry in json["search-results"]["entry"]
        if "dc:title" in entry
    ]

    return Page(
        n_results=number_of_results,
        n_pages=number_of_pages,
        current_page=current_page,
        entries=entries,
    )


def check_api_key_is_expired(
    response: httpx.Response,
) -> bool:
    """Checks if the given response indicates that the API key is expired.

    An API key is expired if the response status code is 429.

    Args:
        response (httpx.Response): Response to check.

    Returns:
        True if the API key is expired, False otherwise.
    """
    return response.status_code == 429


def check_string_is_invalid(
    response: httpx.Response,
) -> bool:
    """Checks if the given response indicates that the string is invalid.

    A string is invalid if the response status code is 400 or 413.

    Args:
        response (httpx.Response): Response to check.

    Returns:
        True if the string is invalid, False otherwise.
    """
    return response.status_code in (400, 413)


def create_clients_list(
    api_keys_list: list[str],
) -> list[httpx.AsyncClient]:
    """Creates a list of async httpx clients that can be used for Scopus queries.

    Args:
        api_keys_list (list[str]): List with the API keys to be used. Each client will use one API Key.

    Returns:
        List of async clients.
    """  # noqa: E501
    return [
        httpx.AsyncClient(
            base_url=SCOPUS_API_URL,
            params={
                "apiKey": api_key,
            },
            timeout=None,
        )
        for api_key in api_keys_list
    ]


class ScopusParams(TypedDict):
    """Data container for the required Scopus Params.

    Attributes:
        query (str): Query to be searched.
        start (int): Paginator parameter.

    Examples:
        >>> p: ScopusParams = {"query": "machine learning", "start": 0}
        >>> p["query"] == "machine learning"
        True
        >>> p["start"] == 0
        True
    """

    query: str
    start: int


def create_params_pagination(
    query: str,
    n_results: int,
) -> list[ScopusParams]:
    """Creates a list of ScopusParams for pagination.

    Args:
        query (str): Query to be searched.
        n_results (int): Number of results returned by Scopus.

    Returns:
        List of ScopusParams.
    """  # noqa: E501
    limited_results = min(5000, n_results)

    paginator = range(1 * 25, limited_results, 25)
    params_list: list[ScopusParams] = [
        {
            "query": query,
            "start": page,
        }
        for page in paginator
    ]

    return params_list


class TooManyJSONDecodeErrors(Exception):
    """Reached the maximum number of attempts on JSONDecodeError."""


class TooManyKeyErrors(Exception):
    """Reached the maximum number of attempts on KeyError."""


class TooManyScopusInternalErrors(Exception):
    """Reached the maximum number of attempts on ScopusInternalError."""


class TooManySSLErrors(Exception):
    """Reached the maximum number of attempts on SSLError."""


class ScopusInternalError(Exception):
    """The response has a status code of 500."""


class InvalidStringError(Exception):
    """The response has a status code of 413 or 400. The search string might be too long."""  # noqa: E501


class OutOfAPIKeysError(Exception):
    """All API keys available are expired."""


def raise_too_many_json_decode_errors() -> NoReturn:
    """Raises a TooManyJSONDecodeErrors exception."""
    raise TooManyJSONDecodeErrors()


def raise_too_many_key_errors() -> NoReturn:
    """Raises a TooManyKeyErrors exception."""
    raise TooManyKeyErrors()


def raise_too_many_scopus_internal_errors() -> NoReturn:
    """Raises a TooManyScopusInternalErrors exception."""
    raise TooManyScopusInternalErrors()


def raise_too_many_ssl_errors() -> NoReturn:
    """Raises a TooManySSLErrors exception."""
    raise TooManySSLErrors()


class ScopusClient:
    """Creates a client that cycles through the available keys to perform efficient searches.

    Attributes:
        DUMMY_QUERY (str): Used when a dummy query is needed. This value is used, for example, to check if the API key is expired.

    To perform a search, use the [`search`][sesg.scopus.client.ScopusClient.search] method.

    !!!note
        You can purge the expired API keys with the `purge_expired_keys` method.
    """  # noqa: E501

    DUMMY_QUERY = "test"

    def __init__(
        self,
        api_keys_list: list[str],
    ) -> None:
        """Initializes the instance.

        Args:
            api_keys_list (list[str]): List with API keys.
        """  # noqa: E501
        self.clients_list = MutableCycle(create_clients_list(api_keys_list))

    def delete_client(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        """Deletes a client from the list of clients.

        Used when the client's API key is expired.

        Args:
            client (httpx.AsyncClient): Client to be deleted.
        """
        self.clients_list.delete_item(client)

    async def fetch(
        self,
        params: ScopusParams,
    ) -> httpx.Response:
        """Sends a request with the given params, if a client is available and returns the response.

        Will recursively retry with another API key if the response's status code is 429.

        Args:
            params (ScopusParams): Dictionary with the fetch parameters.

        Raises:
            OutOfAPIKeysError: If all API keys are expired.
            InvalidStringError: If the string is too long, meaning the response's status code is either 413, 429.

        Returns:
            The response obtained.
        """  # noqa: E501
        try:
            client = next(self.clients_list)
        except StopIteration:
            raise OutOfAPIKeysError()

        response = await client.get("", params=params)  # type: ignore

        if check_string_is_invalid(response):
            raise InvalidStringError()

        if check_api_key_is_expired(response):
            self.delete_client(client)

            return await self.fetch(params)

        return response

    async def fetch_first_page(
        self,
        query: str,
    ) -> tuple[Page, list[ScopusParams]]:
        """Requests for the first page of a query.

        Args:
            query (str): Query to request for the first page.

        Returns:
            A tuple with the parsed response and a list of ScopusParams for pagination.
        """
        params: ScopusParams = {
            "query": query,
            "start": 0,
        }

        res = await self.fetch_and_parse(params)

        params_list = create_params_pagination(query, res.n_results)

        return res, params_list

    @retry(
        stop=stop_after_attempt(MAX_ATTEMPTS_ON_KEY_ERROR),
        retry=retry_if_exception_type(KeyError),
        retry_error_callback=lambda _: raise_too_many_key_errors(),
    )
    @retry(
        stop=stop_after_attempt(MAX_ATTEMPTS_ON_JSON_DECODE_ERROR),
        retry=retry_if_exception_type(JSONDecodeError),
        retry_error_callback=lambda _: raise_too_many_json_decode_errors(),
    )
    @retry(
        stop=stop_after_attempt(MAX_ATTEMPTS_ON_SCOPUS_INTERNAL_ERROR),
        retry=retry_if_exception_type(ScopusInternalError),
        retry_error_callback=lambda _: raise_too_many_scopus_internal_errors(),
    )
    @retry(
        stop=stop_after_attempt(MAX_ATTEMPTS_ON_SSL_ERROR),
        retry=retry_if_exception_type(SSLError),
        retry_error_callback=lambda _: raise_too_many_ssl_errors(),
    )
    async def fetch_and_parse(
        self,
        params: ScopusParams,
    ) -> Page:
        """Makes a request using the given parameters, and parses the response.

        Args:
            params (ScopusParams): Parameters of the request.

        Raises:
            InvalidStringError: If the response has a status code of 400 or 413.
            TooManyJSONDecodeErrors: If the maximum number of attempts on JSONDecodeError is reached.
            TooManyKeyErrors: If the maximum number of attempts on KeyError is reached.
            TooManySSLSErrors: If the maximum number of attempts on SSLError is reached.
            OutOfAPIKeysError: If all API keys are expired.

        Returns:
            A parsed response, meaning a [`Page`][sesg.scopus.client.Page] instance.
        """  # noqa: E501
        response = await self.fetch(params)

        if response.status_code == 500:
            raise ScopusInternalError()

        return parse_response(response)

    async def search(
        self,
        query: str,
        max_concurrent_tasks: int | None = None,
    ) -> AsyncIterable[Page]:
        """Performs concurrent requests to all of the pages of the given query.

        Args:
            query (str): The query to search for.
            max_concurrent_tasks (Optional[int]): The maximum number of concurrently running tasks. If None, will set to the number of pages of the query.

        Raises:
            InvalidStringError: If the response has a status code of 400 or 413.
            TooManyJSONDecodeErrors: If the maximum number of attempts on JSONDecodeError is reached.
            TooManyKeyErrors: If the maximum number of attempts on KeyError is reached.
            OutOfAPIKeysError: If all API keys are expired.

        Yields:
            A [`Page`][sesg.scopus.client.Page] instance.
        """  # noqa: E501
        first_page, params_list = await self.fetch_first_page(query)

        yield first_page

        max_concurrent_tasks = max_concurrent_tasks or max(len(params_list), 1)

        async with aiometer.amap(
            self.fetch_and_parse,
            params_list,
            max_at_once=max_concurrent_tasks,
            max_per_second=len(self.clients_list) * MAX_REQUESTS_PER_SECOND_PER_API_KEY,
        ) as next_pages:
            async for page in next_pages:
                yield page

    async def get_expired_clients(self) -> list[httpx.AsyncClient]:
        """Verifies which clients have expired API keys.

        Returns:
            List of clients with expired API keys.
        """
        params: ScopusParams = {
            "query": ScopusClient.DUMMY_QUERY,
            "start": 0,
        }

        fns = [
            partial(
                client.get,
                "",
                params=params,  # type: ignore
            )
            for client in self.clients_list.items
        ]

        responses = await aiometer.run_all(
            fns,
            max_at_once=len(self.clients_list),
            max_per_second=len(self.clients_list),
        )

        expired_clients: list[httpx.AsyncClient] = []

        for client, response in zip(
            self.clients_list.items,
            responses,
        ):
            if check_api_key_is_expired(response):
                expired_clients.append(client)

        return expired_clients

    async def purge_expired_clients(self):
        """Removes all clients with expired API keys from the list of clients."""
        expired_clients = await self.get_expired_clients()

        for client in expired_clients:
            self.delete_client(client)
