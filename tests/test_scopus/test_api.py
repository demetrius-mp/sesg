from datetime import datetime

import httpx
import pytest
from pytest_httpx import HTTPXMock
from sesg.scopus import api

from .test_utils import simulate_network_latency


def test_api_key_is_expired_should_return_true_when_status_code_is_429():
    r = httpx.Response(status_code=429)

    result = api._api_key_is_expired(response=r)

    assert result is True


def test_api_key_is_expired_should_return_false_when_status_code_is_not_429():
    r = httpx.Response(status_code=200)

    result = api._api_key_is_expired(response=r)

    assert result is False


def test_get_api_key_reset_date_should_return_none_when_response_does_not_have_x_ratelimit_reset_header():
    r = httpx.Response(429)

    result = api._get_api_key_reset_date(response=r)

    assert result is None


def test_get_api_key_reset_date_should_return_datetime_when_response_has_x_ratelimit_reset_header():
    timestamp = 1684782239

    r = httpx.Response(
        429,
        headers={
            "X-RateLimit-Reset": str(timestamp),
        },
    )

    result = api._get_api_key_reset_date(response=r)

    assert result == datetime.fromtimestamp(int(timestamp))


@pytest.mark.asyncio
async def test_fetch_should_raise_timeout_error_when_request_takes_longer_than_3_seconds(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_callback(simulate_network_latency(4))

    req = httpx.Request("GET", "https://test_url")

    async with httpx.AsyncClient() as client:
        with pytest.raises(api.TimeoutError):
            await api._fetch(
                client=client,
                request=req,
                timeout=3,
            )


@pytest.mark.asyncio
async def test_fetch_should_raise_timeout_error_when_request_raises_connect_error(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_exception(httpx.ConnectError("Connection Error"))
    req = httpx.Request("GET", "https://test_url")

    async with httpx.AsyncClient() as client:
        with pytest.raises(api.TimeoutError):
            await api._fetch(
                client=client,
                request=req,
                timeout=3,
            )


@pytest.mark.asyncio
async def test_fetch_should_raise_api_key_expired_error_when_status_code_is_429(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(429)
    req = httpx.Request("GET", "https://test_url")

    async with httpx.AsyncClient() as client:
        with pytest.raises(api.APIKeyExpiredError):
            await api._fetch(
                client=client,
                request=req,
                timeout=3,
            )


@pytest.mark.asyncio
async def test_fetch_should_raise_bad_request_error_when_status_code_is_400(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(400)
    req = httpx.Request("GET", "https://test_url")

    async with httpx.AsyncClient() as client:
        with pytest.raises(api.BadRequestError):
            await api._fetch(
                client=client,
                request=req,
                timeout=3,
            )


@pytest.mark.asyncio
async def test_fetch_should_raise_payload_too_large_error_when_status_code_is_413(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(413)
    req = httpx.Request("GET", "https://test_url")

    async with httpx.AsyncClient() as client:
        with pytest.raises(api.PayloadTooLargeError):
            await api._fetch(
                client=client,
                request=req,
                timeout=3,
            )


@pytest.mark.asyncio
async def test_fetch_should_return_response(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(200)
    req = httpx.Request("GET", "https://test_url")

    async with httpx.AsyncClient() as client:
        response = await api._fetch(
            client=client,
            request=req,
            timeout=3,
        )

    assert isinstance(response, httpx.Response) is True


def test_create_request_should_return_request_with_scopus_url():
    req = api._create_request(
        api_key="",
        query="",
    )

    assert req.url.host == "api.elsevier.com"
    assert req.url.path == "/content/search/scopus"


def test_create_request_should_return_request_with_query_param_start_set_to_0():
    req = api._create_request(
        api_key="",
        query="",
    )

    assert req.url.params.get("start") == "0"


def test_create_request_should_return_request_with_query_param_api_key_set_to_user123():
    req = api._create_request(
        api_key="user123",
        query="",
    )

    assert req.url.params.get("apiKey") == "user123"


def test_create_request_should_return_request_with_query_param_query_set_to_machine_learning():
    req = api._create_request(
        api_key="user123",
        query="machine learning",
    )

    assert req.url.params.get("query") == "machine learning"


def test_parse_response_should_return_success_response_instance_with_81_pages():
    response = httpx.Response(
        200,
        json={
            "search-results": {
                "opensearch:totalResults": 2001,
                "opensearch:startIndex": 0,
                "entry": [],
            }
        },
    )

    result = api._parse_response(response=response)

    assert result.number_of_pages == 81


def test_parse_response_should_return_success_response_instance_with_200_pages():
    response = httpx.Response(
        200,
        json={
            "search-results": {
                "opensearch:totalResults": 6000,
                "opensearch:startIndex": 0,
                "entry": [],
            }
        },
    )

    result = api._parse_response(response=response)

    assert result.number_of_pages == 200


def test_parse_response_should_return_only_success_response_entries_with_dc_title_key():
    response = httpx.Response(
        200,
        json={
            "search-results": {
                "opensearch:totalResults": 2,
                "opensearch:startIndex": 0,
                "entry": [
                    {
                        "dc:title": "",
                        "dc:identifier": "",
                    },
                    {
                        "dc:identifier": "",
                    },
                ],
            }
        },
    )

    result = api._parse_response(response=response)

    assert len(result.entries) == 1


def test_parse_headers_should_accept_x_ratelimit_remaining_none():
    headers = httpx.Headers(
        {
            "x-els-status": "",
            "x-ratelimit-reset": "",
        }
    )

    result = api.parse_headers(headers=headers)

    assert result.x_ratelimit_remaining is None


def test_parse_headers_should_accept_x_ratelimit_reset_none():
    headers = httpx.Headers(
        {
            "x-els-status": "",
        }
    )

    result = api.parse_headers(headers=headers)

    assert result.x_ratelimit_reset is None


@pytest.mark.asyncio
async def test_search_should_do_2_requests(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(
        200,
        json={
            "search-results": {
                "opensearch:totalResults": 27,
                "opensearch:startIndex": 0,
                "entry": [],
            }
        },
    )

    async for _ in api.search(
        api_key="user",
        page=0,
        query="code",
        timeout=3,
    ):
        ...

    reqs = httpx_mock.get_requests()

    assert len(reqs) == 2
