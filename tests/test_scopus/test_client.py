import pytest
from pytest_httpx import HTTPXMock
from sesg import scopus

from .test_utils import simulate_network_latency


@pytest.fixture()
def scopus_client():
    api_keys = ["1", "2", "3"]
    timeout = 1
    timeout_retries = 4

    client = scopus.ScopusClient(
        api_keys=api_keys,
        timeout=timeout,
        timeout_retries=timeout_retries,
    )

    return client


def test_scopus_client_attributes():
    api_keys = ["1", "2", "3"]
    timeout = 3
    timeout_retries = 4

    client = scopus.ScopusClient(
        api_keys=api_keys,
        timeout=timeout,
        timeout_retries=timeout_retries,
    )

    assert client.api_keys == api_keys
    assert client.timeout == timeout
    assert client.timeout_retries == timeout_retries

    query = "code"
    client.search(query)
    assert client.current_query == query


@pytest.mark.asyncio
async def test_scopus_client_should_yield_api_key_expired_response_when_first_api_key_is_expired(
    scopus_client: scopus.ScopusClient,
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(
        429,
        url="https://api.elsevier.com/content/search/scopus?apiKey=1&query=code&start=0",
    )

    iterator = scopus_client.search("code")

    result = await iterator.__anext__()

    assert isinstance(result, scopus.APIKeyExpiredResponse) is True


@pytest.mark.asyncio
async def test_scopus_client_should_yield_success(
    scopus_client: scopus.ScopusClient,
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(
        200,
        url="https://api.elsevier.com/content/search/scopus?apiKey=1&query=code&start=0",
        json={
            "search-results": {
                "opensearch:totalResults": 13,
                "opensearch:startIndex": 0,
                "entry": [],
            }
        },
    )

    iterator = scopus_client.search("code")

    result = await iterator.__anext__()

    assert isinstance(result, scopus.SuccessResponse) is True


@pytest.mark.asyncio
async def test_scopus_client_should_raise_payload_too_large_error_when_status_code_is_413(
    scopus_client: scopus.ScopusClient,
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(
        413,
    )

    iterator = scopus_client.search("code")

    with pytest.raises(scopus.PayloadTooLargeError):
        await iterator.__anext__()


@pytest.mark.asyncio
async def test_scopus_client_should_raise_bad_request_error_when_status_code_is_400(
    scopus_client: scopus.ScopusClient,
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(
        400,
    )

    iterator = scopus_client.search("code")

    with pytest.raises(scopus.BadRequestError):
        await iterator.__anext__()


@pytest.mark.asyncio
async def test_scopus_client_should_raise_out_of_api_keys_error_when_all_api_keys_are_expired(
    scopus_client: scopus.ScopusClient,
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(429)

    with pytest.raises((scopus.OutOfAPIKeysError, scopus.api.APIKeyExpiredError)):
        async for r in scopus_client.search("code"):
            assert isinstance(r, scopus.APIKeyExpiredResponse) is True


def test_scopus_client_current_query_should_change_if_search_is_called_with_another_query(
    scopus_client: scopus.ScopusClient,
):
    query = "code"
    scopus_client.search(query)
    assert scopus_client.current_query == query

    query = "smells"
    scopus_client.search(query)
    assert scopus_client.current_query == query


@pytest.mark.asyncio
async def test_scopus_client_current_page_should_increment(
    scopus_client: scopus.ScopusClient,
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(
        200,
        url="https://api.elsevier.com/content/search/scopus?apiKey=1&query=code&start=0",
        json={
            "search-results": {
                "opensearch:totalResults": 55,
                "opensearch:startIndex": 0,
                "entry": [],
            }
        },
    )

    httpx_mock.add_response(
        200,
        url="https://api.elsevier.com/content/search/scopus?apiKey=1&query=code&start=25",
        json={
            "search-results": {
                "opensearch:totalResults": 55,
                "opensearch:startIndex": 25,
                "entry": [],
            }
        },
    )

    httpx_mock.add_response(
        200,
        url="https://api.elsevier.com/content/search/scopus?apiKey=1&query=code&start=50",
        json={
            "search-results": {
                "opensearch:totalResults": 55,
                "opensearch:startIndex": 50,
                "entry": [],
            }
        },
    )

    seen_pages: set[int] = set()
    async for r in scopus_client.search("code"):
        if isinstance(r, scopus.SuccessResponse):
            assert scopus_client.current_page == r.current_page
            assert scopus_client.current_page not in seen_pages
            seen_pages.add(scopus_client.current_page)

    assert seen_pages == set((1, 2, 3))


@pytest.mark.asyncio
async def test_scopus_client_should_raise_exceeded_timeout_retries_error_if_did_4_timed_out_requests(
    scopus_client: scopus.ScopusClient,
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_callback(simulate_network_latency(2))

    last_timeout_retry = -1
    with pytest.raises(scopus.ExceededTimeoutRetriesError):
        async for r in scopus_client.search("code"):
            assert isinstance(r, scopus.TimeoutResponse)

            assert r.timeout_retry > last_timeout_retry
            last_timeout_retry = r.timeout_retry
