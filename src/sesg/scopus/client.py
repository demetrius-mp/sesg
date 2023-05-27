"""This module provides a Scopus client that efficiently uses your API keys.

It is highly recommended to use [`trio`](https://trio.readthedocs.io/) to manage the async functions
as it is much faster.

## Usage example

```python
import trio
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn

KEYS: list[str] = [...]  # list of API keys

async def main():
    client = ScopusClient(KEYS)

    with Progress(
        TextColumn(
            "[progress.description]{task.description}: {task.completed} of {task.total}"
        ),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        for string in ["code smell", "machine learning", "covid"]:
            task = progress.add_task(
                "Searching",
            )

            results: list[SuccessResponse.Entry] = []

            try:
                async for page in client.search(string):
                    progress.update(
                        task,
                        advance=1,
                        total=page.n_pages,
                        refresh=True,
                    )

                    results.extend(page.entries)

            except InvalidStringError:
                print("The following string raised an InvalidStringError")
                print(string)

            progress.remove_task(task)
            # save to database or whatever



trio.run(main)
```
"""  # noqa: E501

import math
from dataclasses import dataclass
from functools import partial
from typing import Any, AsyncIterable

import aiometer
import httpx
from typing_extensions import TypedDict

from .mutable_cycle import MutableCycle


SCOPUS_API_URL = "https://api.elsevier.com/content/search/scopus"


@dataclass(frozen=True)
class SuccessResponse:
    """A successfull Scopus Response.

    Args:
        number_of_results (int): Number of results for this query. Notice that even if it displays more than 5000 results, Scopus will limit to retrieve only 5000.
        number_of_pages (int): Number of pages that needs to be fetched to get all results. Limited to 200 due to Scopus API 5000 entries limit.
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
) -> SuccessResponse:
    """Parses a Scopus API response.

    Args:
        response (httpx.Response): A Scopus API response.

    Returns:
        A SuccessResponse instance.
    """  # noqa: E501
    json = response.json()

    number_of_results = int(json["search-results"]["opensearch:totalResults"])
    start_index = int(json["search-results"]["opensearch:startIndex"])
    current_page = math.floor(start_index / 25) + 1
    number_of_pages = min(math.ceil(number_of_results / 25), 200)

    entries = [
        SuccessResponse.Entry(
            title=entry["dc:title"],
            scopus_id=entry["dc:identifier"],
            cited_by_count=entry.get("citedby-count", None),
            _rest=entry,
        )
        for entry in json["search-results"]["entry"]
        if "dc:title" in entry
    ]

    return SuccessResponse(
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


class InvalidStringError(Exception):
    """The response has a status code of 413 or 400. The search string might be too long."""  # noqa: E501


class OutOfAPIKeysError(Exception):
    """All API keys available are expired."""


class ScopusClient:
    """Creates a client that cycles through the available keys to perform efficient searches.

    Attributes:
        DUMMY_QUERY (str): Used when a dummy query is needed. This value is used, for example, to check if the API key is expired.

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

        Will recursively retry if the response's status code is 429.

        Args:
            params (ScopusParams): Dictionary with the fetch parameters.

        Raises:
            OutOfAPIKeys: If all API keys are expired.
            InvalidStringError: If the string is too long, meaning the response's status code is either 413, 429.

        Returns:
            The response obtained.
        """  # noqa: E501
        try:
            client = next(self.clients_list)
        except StopIteration:
            raise OutOfAPIKeysError()

        response = await client.get("", params=params)  # type: ignore

        if response.status_code in (400, 413):
            raise InvalidStringError()

        if response.status_code == 429:
            self.delete_client(client)

            return await self.fetch(params)

        return response

    async def fetch_first_page(
        self,
        query: str,
    ):
        """Requests for the first page of a query using the given client.

        Args:
            client (httpx.AsyncClient): Client with an API key.
            query (str): Query to request for the first page.
        """
        params: ScopusParams = {
            "query": query,
            "start": 0,
        }

        res = await self.fetch_and_parse(params)

        paginator = range(1 * 25, min(5000, res.n_results), 25)
        params_list: list[ScopusParams] = [
            {
                "query": query,
                "start": page,
            }
            for page in paginator
        ]

        return res, params_list

    async def fetch_and_parse(
        self,
        params: ScopusParams,
    ) -> SuccessResponse:
        """Makes a request using the given parameters, and parses the response.

        Args:
            params (ScopusParams): Parameters of the request.

        Raises:
            InvalidStringError: If the response has a status code of 400 or 413.

        Returns:
            A parsed response, meaning an instance of SuccessResponse.
        """  # noqa: E501
        # params, client = args

        response = await self.fetch(params)

        return parse_response(response)

    async def search(
        self,
        query: str,
    ) -> AsyncIterable[SuccessResponse]:
        """Performs concurrent requests to all of the pages of the given query.

        Args:
            query (str): The query to search for.

        Yields:
            A SuccessResponse instance.
        """
        first_page, params_list = await self.fetch_first_page(
            query,
        )

        yield first_page

        async with aiometer.amap(
            self.fetch_and_parse,
            params_list,
            max_at_once=len(self.clients_list) * 12,
            max_per_second=len(self.clients_list) * 8,
        ) as next_pages:
            async for page in next_pages:
                yield page

    async def get_expired_clients(self) -> list[httpx.AsyncClient]:
        """Verifies which clients have expired API keys.

        Yield:
            Clients with expired API keys.
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
