"""
Scopus API communication module.

This module provides a python interface to perform raw
Scopus API requests. It does so by defining clear exceptions,
and a data container for a successfull response.

Attributes:
    SCOPUS_API_URL (str): Base URL for the Scopus API.
"""

import asyncio
import math
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from typing import AsyncIterator, List, Optional, Union

import aiometer
import httpx


# base URL for Scopus API.
SCOPUS_API_URL = "https://api.elsevier.com/content/search/scopus"


@dataclass
class SuccessResponse:
    """A successfull Scopus Response

    Args:
        number_of_results (int): Number of results for this query.
        number_of_pages (int): Number of pages that needs to be fetched to get all results. Limited to 200 due to Scopus API 5000 entries limit.
        current_page (int): Current page being fetched.
        entries (List[Entry]): Studies returned from the API.
    """  # noqa: E501

    @dataclass
    class Entry:
        """A study entry returned from the API.

        Args:
            title (str): The title of the study.
        """

        title: str

    number_of_results: int
    number_of_pages: int
    current_page: int
    entries: List[Entry]


class TimeoutError(Exception):
    """The request took too long."""


class APIKeyExpiredError(Exception):
    """The API key is expired, meaning it has been used over 20000 times in less than a week"""  # noqa: E501

    resets_at: Optional[datetime]

    def __init__(
        self,
        *,
        resets_at: Optional[datetime] = None,
    ) -> None:
        self.resets_at = resets_at


class PayloadTooLargeError(Exception):
    """The response has a status code of 413. Probably the search string is too long."""


def _api_key_is_expired(
    *,
    response: httpx.Response,
) -> bool:
    """Checks if a Scopus API key is expired, given the response of a Scopus Request.

    Args:
        response (httpx.Response): A Scopus API response.

    Returns:
        True if the API key is expired, False otherwise.
    """  # noqa: E501
    remaining = response.headers.get("x-ratelimit-remaining")
    remaining_condition = remaining is not None and int(remaining) <= 0

    els_status_condition = (
        response.headers.get("x-els-status") == "QUOTA_EXCEEDED - Quota Exceeded"
    )
    return remaining_condition or els_status_condition


def _get_api_key_reset_date(
    *,
    response: httpx.Response,
) -> Union[None, datetime]:
    """Given a Scopus API response, will try do determine the reset date using the response headers.

    Args:
        response (httpx.Response): A Scopus API response.

    Returns:
        A datetime representing the reset date, or None if it wasn't able to determine it.
    """  # noqa: E501
    timestamp = response.headers.get("X-RateLimit-Reset")
    if timestamp is None:
        return None

    return datetime.fromtimestamp(int(timestamp))


async def _fetch(
    client: httpx.AsyncClient,
    timeout: float,
    request: httpx.Request,
) -> httpx.Response:
    """Fetches the given request, and if needed, raises a custom Exception.

    Args:
        client (httpx.AsyncClient): Async client that will fetch the request.
        timeout (int): How long to wait before assuming the request timed out.
        request (httpx.Request): The request to fetch.

    Raises:
        TimeoutError: If the request takes longer than the given `timeout`.
        APIKeyExpiredError: If the response has a header indicating that the API Key is expired.
        PayloadTooLargeError: If the response status code is 413. Indicates that the search string is too large.

    Returns:
        A successfull response.
    """  # noqa: E501
    try:
        task = client.send(request)
        response = await asyncio.wait_for(
            fut=task,
            timeout=timeout,
        )

    except (asyncio.TimeoutError, httpx.ConnectError):
        raise TimeoutError()

    if _api_key_is_expired(response=response):
        resets_at = _get_api_key_reset_date(response=response)
        raise APIKeyExpiredError(resets_at=resets_at)

    if response.status_code == 413:
        raise PayloadTooLargeError()

    return response


def _create_request(
    *,
    api_key: str,
    query: str,
    start: Optional[int] = 0,
) -> httpx.Request:
    """Creates a `httpx.Request` for Scopus API.

    Args:
        api_key (str): A Scopus API key.
        query (str): Search string to use.
        start (Optional[int]): Start parameter, used for pagination.

    Returns:
        A request object with the given information.
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
        SCOPUS_API_URL,
        params=params,
        headers=headers,
    )

    return request


def _parse_response(
    *,
    response: httpx.Response,
) -> SuccessResponse:
    """Parses a Scopus API response.

    Args:
        response (httpx.Response): A Scopus API response.

    Returns:
        A SuccessResponse instance
    """  # noqa: E501
    json = response.json()

    number_of_results = int(json["search-results"]["opensearch:totalResults"])
    start_index = int(json["search-results"]["opensearch:startIndex"])
    current_page = math.floor(start_index / 25) + 1
    number_of_pages = min(math.ceil(number_of_results / 25), 200)

    entries = [
        SuccessResponse.Entry(
            title=entry["dc:title"],
        )
        for entry in json["search-results"]["entry"]
        if "dc:title" in entry
    ]

    return SuccessResponse(
        number_of_results=number_of_results,
        number_of_pages=number_of_pages,
        current_page=current_page,
        entries=entries,
    )


async def search(
    *,
    api_key: str,
    query: str,
    timeout: float,
    page: int,
) -> AsyncIterator[SuccessResponse]:
    """Performs Scopus API calls, in a manner that will return
    all available results, which is at most 5000.

    Args:
        api_key (str): Valid Scopus API key.
        query (str): Query to search for.
        timeout (int): How long to wait for the request to complete.
        page (int): Page where to start the search.

    Raises:
        TimeoutError: If the request takes longer than the given `timeout`.
        APIKeyExpiredError: If the response has a header indicating that the API Key is expired.
        PayloadTooLargeError: If the response status code is 413. Indicates that the search string is too large.

    Yields:
        Async iterator that yields each page found.
    """  # noqa: E501
    client = httpx.AsyncClient()

    first_request = _create_request(
        api_key=api_key,
        query=query,
        start=page * 25,
    )

    response = await _fetch(
        client=client,
        request=first_request,
        timeout=timeout,
    )

    result = _parse_response(response=response)

    yield result

    paginator = range((page + 1) * 25, min(5000, result.number_of_results), 25)
    requests = [
        _create_request(
            api_key=api_key,
            query=query,
            start=page_start,
        )
        for page_start in paginator
    ]

    async with aiometer.amap(
        partial(_fetch, client, timeout),
        requests,
        max_per_second=7,
        max_at_once=7,
    ) as result:
        async for response in result:
            result = _parse_response(response=response)

            yield result