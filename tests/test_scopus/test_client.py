import httpx
import pytest
from pytest_httpx import HTTPXMock
from sesg.scopus import client as client_module


def test_parse_response_should_return_response_with_2_pages():
    response = httpx.Response(
        status_code=200,
        json={
            "search-results": {
                "opensearch:totalResults": 27,
                "opensearch:startIndex": 0,
                "entry": [
                    {
                        "dc:title": "",
                        "dc:identifier": "",
                    },
                ]
                * 25,
            }
        },
    )

    parsed = client_module._parse_response(response)

    assert parsed.n_results == 27
    assert parsed.n_pages == 2
    assert len(parsed.entries) == 25


def test_check_api_key_is_expired_should_return_true_when_response_has_status_code_429():
    response = httpx.Response(429)

    assert client_module._check_api_key_is_expired(response) is True


def test_check_string_is_invalid_should_return_true_when_response_has_status_code_400():
    response = httpx.Response(400)

    assert client_module._check_string_is_invalid(response) is True


def test_check_string_is_invalid_should_return_true_when_response_has_status_code_413():
    response = httpx.Response(413)

    assert client_module._check_string_is_invalid(response) is True


def test_create_clients_list_should_create_4_clients():
    api_keys_list = ["k1", "k2", "k3", "k4"]

    clients_list = client_module._create_clients_list(api_keys_list)

    assert len(clients_list) == 4


def test_create_clients_list_should_return_list_of_httpx_async_clients():
    api_keys_list = ["k1", "k2", "k3", "k4"]

    clients_list = client_module._create_clients_list(api_keys_list)

    assert all(isinstance(client, httpx.AsyncClient) for client in clients_list)


def test_create_clients_list_should_assign_api_keys_to_clients():
    api_keys_list = ["k1", "k2", "k3", "k4"]

    clients_list = client_module._create_clients_list(api_keys_list)

    for client, key in zip(clients_list, api_keys_list):
        assert client.params.get("apiKey") == key


def test_create_params_pagination_should_create_2_params():
    params = client_module._create_params_pagination(
        query="",
        n_results=54,
    )

    assert len(params) == 2


def test_create_params_pagination_should_create_all_params_with_same_query():
    query = "code smell"

    params = client_module._create_params_pagination(
        query=query,
        n_results=54,
    )

    assert all(param["query"] == query for param in params)


def test_create_params_pagination_should_return_first_param_with_start_value_25():
    params = client_module._create_params_pagination(
        query="",
        n_results=54,
    )

    assert params[0]["start"] == 25


def test_create_params_pagination_should_increment_start_value_by_25():
    params = client_module._create_params_pagination(
        query="",
        n_results=54,
    )

    assert params[0]["start"] == 25
    assert params[1]["start"] == 50


def test_create_params_pagination_should_limit_to_199_pages():
    params = client_module._create_params_pagination(
        query="",
        n_results=10000,
    )

    assert len(params) == 199


def test_scopus_client_should_have_4_clients():
    scopus_client = client_module.ScopusClient(
        api_keys_list=["k1", "k2", "k3", "k4"],
    )

    assert len(scopus_client.clients_list) == 4


def test_scopus_client_delete_client_should_remove_client_from_clients_list():
    scopus_client = client_module.ScopusClient(
        api_keys_list=["k1", "k2", "k3", "k4"],
    )

    assert len(scopus_client.clients_list) == 4

    first_client = next(scopus_client.clients_list)

    scopus_client._delete_client(first_client)

    assert all(client != first_client for client in scopus_client.clients_list.items)

    assert len(scopus_client.clients_list) == 3


@pytest.mark.asyncio
async def test_scopus_search_fetch_should_delete_expired_client(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(
        200,
        json={
            "search-results": {
                "opensearch:totalResults": 27,
                "opensearch:startIndex": 0,
                "entry": [
                    {
                        "dc:title": "",
                        "dc:identifier": "",
                    },
                ],
            }
        },
    )

    httpx_mock.add_response(
        429,
        url="https://api.elsevier.com/content/search/scopus/?apiKey=k2&query=code&start=25",
    )

    client = client_module.ScopusClient(["k1", "k2", "k3", "k4"])

    async for _ in client.search("code"):
        pass

    assert len(client.clients_list) == 3


@pytest.mark.asyncio
async def test_scopus_search_fetch_should_raise_out_of_api_keys_error_when_all_clients_are_expired(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(429)

    client = client_module.ScopusClient(["k1", "k2", "k3", "k4"])

    with pytest.raises(client_module.OutOfAPIKeysError):
        async for _ in client.search("code smell"):
            pass


@pytest.mark.asyncio
async def test_scopus_search_fetch_should_raise_invalid_string_error_when_status_code_is_400(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(400)

    client = client_module.ScopusClient(["k1", "k2"])

    with pytest.raises(client_module.InvalidStringError):
        async for _ in client.search("code"):
            pass


@pytest.mark.asyncio
async def test_scopus_search_fetch_should_raise_invalid_string_error_when_status_code_is_413(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(413)

    client = client_module.ScopusClient(["k1", "k2"])

    with pytest.raises(client_module.InvalidStringError):
        async for _ in client.search("code"):
            pass


@pytest.mark.asyncio
async def test_scopus_search_fetch_should_return_parseable_response(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(
        200,
        json={
            "search-results": {
                "opensearch:totalResults": 25,
                "opensearch:startIndex": 0,
                "entry": [
                    {
                        "dc:title": "",
                        "dc:identifier": "",
                    },
                ]
                * 25,
            }
        },
    )

    client = client_module.ScopusClient(["k1", "k2"])

    response = await client._fetch(
        {
            "query": "code",
            "start": 0,
        }
    )

    parsed = client_module._parse_response(response)

    assert parsed.n_pages == 1


@pytest.mark.asyncio
async def test_scopus_search_search_should_yield_2_pages(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(
        200,
        json={
            "search-results": {
                "opensearch:totalResults": 35,
                "opensearch:startIndex": 0,
                "entry": [
                    {
                        "dc:title": "",
                        "dc:identifier": "",
                    },
                ],
            }
        },
    )

    client = client_module.ScopusClient(["k1", "k2"])

    pages_list: list[client_module.Page] = []
    async for page in client.search("code"):
        pages_list.append(page)

    assert len(pages_list) == 2


@pytest.mark.asyncio
async def test_scopus_search_search_should_yield_3_pages_even_if_one_key_expired(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(
        429,
        url="https://api.elsevier.com/content/search/scopus/?apiKey=k1&query=code&start=0",
    )

    httpx_mock.add_response(
        200,
        url="https://api.elsevier.com/content/search/scopus/?apiKey=k2&query=code&start=0",
        json={
            "search-results": {
                "opensearch:totalResults": 60,
                "opensearch:startIndex": 0,
                "entry": [
                    {
                        "dc:title": "first page",
                        "dc:identifier": "first page",
                    },
                ]
                * 25,
            }
        },
    )

    httpx_mock.add_response(
        200,
        url="https://api.elsevier.com/content/search/scopus/?apiKey=k2&query=code&start=25",
        json={
            "search-results": {
                "opensearch:totalResults": 60,
                "opensearch:startIndex": 25,
                "entry": [
                    {
                        "dc:title": "second page",
                        "dc:identifier": "second page",
                    },
                ]
                * 25,
            }
        },
    )

    httpx_mock.add_response(
        200,
        url="https://api.elsevier.com/content/search/scopus/?apiKey=k2&query=code&start=50",
        json={
            "search-results": {
                "opensearch:totalResults": 60,
                "opensearch:startIndex": 50,
                "entry": [
                    {
                        "dc:title": "third page",
                        "dc:identifier": "third page",
                    },
                ]
                * 10,
            }
        },
    )

    client = client_module.ScopusClient(["k1", "k2"])

    pages_list: list[client_module.Page] = []
    seen_pages = [False] * 3

    async for page in client.search("code"):
        pages_list.append(page)
        seen_pages[page.current_page - 1] = True

    assert len(pages_list) == 3
    assert all(seen_pages)


@pytest.mark.asyncio
async def test_scopus_search_get_expired_clients_should_return_2_clients(
    httpx_mock: HTTPXMock,
):
    dummy_query = client_module.ScopusClient.DUMMY_QUERY

    httpx_mock.add_response(
        200,
        url=f"https://api.elsevier.com/content/search/scopus/?apiKey=k2&query={dummy_query}&start=0",
    )

    httpx_mock.add_response(
        429,
        url=f"https://api.elsevier.com/content/search/scopus/?apiKey=k1&query={dummy_query}&start=0",
    )

    httpx_mock.add_response(
        429,
        url=f"https://api.elsevier.com/content/search/scopus/?apiKey=k3&query={dummy_query}&start=0",
    )

    client = client_module.ScopusClient(["k1", "k2", "k3"])

    expired_clients = await client._get_expired_clients()
    for client in expired_clients:
        assert client.params.get("apiKey") != "k2"

    assert len(expired_clients) == 2


@pytest.mark.asyncio
async def test_scopus_search_purge_expired_clients_should_purge_2_clients(
    httpx_mock: HTTPXMock,
):
    dummy_query = client_module.ScopusClient.DUMMY_QUERY

    httpx_mock.add_response(
        200,
        url=f"https://api.elsevier.com/content/search/scopus/?apiKey=k2&query={dummy_query}&start=0",
    )

    httpx_mock.add_response(
        429,
        url=f"https://api.elsevier.com/content/search/scopus/?apiKey=k1&query={dummy_query}&start=0",
    )

    httpx_mock.add_response(
        429,
        url=f"https://api.elsevier.com/content/search/scopus/?apiKey=k3&query={dummy_query}&start=0",
    )

    client = client_module.ScopusClient(["k1", "k2", "k3"])

    await client.purge_expired_clients()

    assert len(client.clients_list) == 1
    assert next(client.clients_list).params.get("apiKey") == "k2"
