"""Provides an abstract class that implements multi client usage to make faster searches.

This code is based on a ChatGPT's answer to the following prompt:

> In python, how to create a queue that executes exactly N async tasks at the same time in parallel?

# Usage example

The example below will display one progress bar for each client, which will show the pagination progress.
It will also display another overall progress bar, showing how many strings are left.

```python
import sys
from rich.progress import Progress

async def main():
    api_keys_list: list[str] = []
    search_strings_list: list[str] = []
    n_clients = 5

    clients_list = create_clients_list(
        api_keys_list=api_keys_list,
        n_clients=n_clients,
    )

    class MultiClientScopusSearch(MultiClientScopusSearchAbstractClass):
        def __init__(
            self,
            clients_list: list[ScopusClient],
            search_strings_list: list[str],
            progress: Progress,
        ) -> None:
            super().__init__(clients_list, search_strings_list)

            self.progress = progress
            self.overall_progress_task = progress.add_task(
                "Overall progress",
                total=len(self.search_strings_list),
            )
            self.clients_progress_tasks = [
                progress.add_task(
                    description=f"Client {i + 1}",
                )
                for i in range(len(self.clients_list))
            ]

        def on_search_initialize(
            self,
            client_index: int,
            search_string_index: int,
        ):
            description = (
                f"Client {client_index + 1} "
                f"(String {search_string_index + 1} of {len(self.search_strings_list)})"  # noqa: E501
            )

            self.progress.update(
                self.clients_progress_tasks[client_index],
                description=description,
            )
            self.progress.advance(self.clients_progress_tasks[client_index])

        def on_first_success_response(
            self,
            client_index: int,
            data: SuccessResponse,
        ):
            self.progress.update(
                self.clients_progress_tasks[client_index],
                total=data.number_of_pages,
                refresh=True,
            )

        def on_api_key_expired_response(
            self,
            client_index: int,
            data: APIKeyExpiredResponse,
        ):
            print(f"API Key {data.api_key} ")

        def on_timeout_response(
            self,
            client_index: int,
            search_string_index: int,
            attempts_left: int,
            data: TimeoutResponse,
        ):
            print(
                f"Client {client_index + 1}: "
                f"Timed out on page {data.timed_out_page} "
                f"of string {search_string_index + 1}. "
                f"{attempts_left} attempts left."
            )

        def on_bad_request_error(
            self,
            client_index: int,
            search_string: str,
            error: BadRequestError,
        ):
            print("The following string raised a BadRequestError")
            print(search_string)

        def on_payload_too_large_error(
            self,
            client_index: int,
            search_string: str,
            error: PayloadTooLargeError,
        ):
            print("The following string raised a BadRequestError")
            print(search_string)

        def on_exceeded_timeout_retries_error(
            self,
            client_index: int,
            error: ExceededTimeoutRetriesError,
        ):
            print("Exceeded the maximum number of timeout retries in a row.")
            sys.exit()

        def on_out_of_api_keys_error(
            self,
            client_index: int,
            error: OutOfAPIKeysError,
        ):
            print("Ran out of API keys.")
            sys.exit()

        def on_search_complete(
            self,
            client_index: int,
            search_string_index: int,
            results: list[SuccessResponse.Entry],
        ):
            # extract metrics, save to database, do your thing

            self.progress.reset(self.clients_progress_tasks[client_index])

        def on_all_complete(self):
            for t in self.clients_progress_tasks:
                self.progress.remove_task(t)

            self.progress.remove_task(self.overall_progress_task)

        def on_all_start(self):
            ...

        def on_success_response(
            self,
            client_index: int,
            data: SuccessResponse,
        ):
            self.progress.advance(self.clients_progress_tasks[client_index])

    with Progress(
        TextColumn(
            "[progress.description]{task.description}: {task.completed} of {task.total}"  # noqa: E501
        ),
        BarColumn(),
        TaskProgressColumn(),
    )  as progress:
        multi_client = MultiClientScopusSearch(
            clients_list=clients_list,
            progress=progress,
            search_strings_list=search_strings_list,
        )

        await multi_client.start()


asyncio.run(main())
```
"""  # noqa: E501

import asyncio
from abc import ABC, abstractmethod

from more_itertools import divide

from .api import BadRequestError, PayloadTooLargeError, SuccessResponse
from .client import (
    APIKeyExpiredResponse,
    ExceededTimeoutRetriesError,
    OutOfAPIKeysError,
    ScopusClient,
    TimeoutResponse,
)


class NoClientsAvailableError(Exception):
    """Raised when all clients are being used."""


def create_clients_list(
    api_keys_list: list[str],
    n_clients: int,
    timeout: float,
    timeout_retries: int,
) -> list[ScopusClient]:
    """Creates a list of clients, where each client has a disjoint set of API keys.

    Args:
        api_keys_list (list[str]): List of Scopus API keys.
        n_clients (int): Number of clients to create.
        timeout (float): Time in seconds to wait before assuming the request timed out.
        timeout_retries (int): Number of times to retry a timed out request in a row.

    Returns:
        List of Scopus Clients instances.
    """
    return [
        ScopusClient(
            api_keys=list(api_keys_group),
            timeout=timeout,
            timeout_retries=timeout_retries,
        )
        for api_keys_group in divide(n_clients, api_keys_list)
    ]


class MultiClientScopusSearchAbstractClass(ABC):
    """Abstract Class that implements a Multiple Client strategy."""

    def __init__(
        self,
        clients_list: list[ScopusClient],
        search_strings_list: list[str],
    ) -> None:
        """Initializes a MultiClientScopusSearch instance.

        The order in which the hooks are executed is the following:

        1. `on_all_start` (once)
        2. `on_search_initialize` (once per search string)
        3. `on_first_success_response` (once per search string)
        4. `on_success_response` (once per search string)
        5. `on_search_complete` (once per search string)
        6. `on_all_complete` (once)

        The other hooks may happen between `2` and `5`.

        Args:
            clients_list (list[ScopusClient]): List of clients.
            search_strings_list (list[str]): List of search strings to use.
        """  # noqa: E501
        self.clients_list = clients_list
        self.search_strings_list = search_strings_list

        self.clients_in_use = [False] * len(self.clients_list)
        self.queue: asyncio.Queue[int] = asyncio.Queue(len(self.search_strings_list))
        self.semaphore = asyncio.Semaphore(len(self.clients_list))

    @abstractmethod
    def on_api_key_expired_response(
        self,
        client_index: int,
        data: APIKeyExpiredResponse,
    ):
        """Hook to execute when the response indicates an expired API key.

        Args:
            client_index (int): Index of the client that executed this hook.
            data (APIKeyExpiredResponse): The response.
        """  # noqa: E501
        ...

    @abstractmethod
    def on_timeout_response(
        self,
        client_index: int,
        search_string_index: int,
        attempts_left: int,
        data: TimeoutResponse,
    ):
        """Hook to execute when the request timed out.

        Args:
            client_index (int): Index of the client that executed this hook.
            search_string_index (int): Index of the search string that executed this hook.
            attempts_left (int): Number of retry attempts left.
            data (TimeoutResponse): The response.
        """  # noqa: E501
        ...

    @abstractmethod
    def on_all_start(self):
        """Hook to execute before clients are initialized."""
        ...

    @abstractmethod
    def on_search_initialize(
        self,
        client_index: int,
        search_string_index: int,
    ):
        """Hook to execute before `client.search` call.

        Args:
            client_index (int): Index of the client that executed this hook.
            search_string_index (int): Index of the search string that executed this hook.
        """  # noqa: E501
        ...

    @abstractmethod
    def on_first_success_response(
        self,
        client_index: int,
        data: SuccessResponse,
    ):
        """Hook to execute when receives a successfull response for the first time.

        Notice that this hook is executed before
        [`on_success_response`][sesg.scopus.MultiClientScopusSearchAbstractClass.on_success_response],
        meaning that on the first success, both of these hooks will be executed.

        Args:
            client_index (int): Index of the client that executed this hook.
            data (SuccessResponse): The response.
        """  # noqa: E501
        ...

    @abstractmethod
    def on_success_response(
        self,
        client_index: int,
        data: SuccessResponse,
    ):
        """Hook to execute when the response is successfull.

        Args:
            client_index (int): Index of the client that executed this hook.
            data (SuccessResponse): The response.
        """
        ...

    @abstractmethod
    def on_bad_request_error(
        self,
        client_index: int,
        search_string: str,
        error: BadRequestError,
    ):
        """Hook to execute when a bad request occurs.

        Args:
            client_index (int): Index of the client that executed this hook.
            search_string (str): Search string that raised this error.
            error (BadRequestError): The error.

        """
        ...

    @abstractmethod
    def on_payload_too_large_error(
        self,
        client_index: int,
        search_string: str,
        error: PayloadTooLargeError,
    ):
        """Hook to execute when the payload is too large.

        Args:
            client_index (int): Index of the client that executed this hook.
            search_string (str): Search string that raised this error.
            error (PayloadTooLargeError): The error.
        """
        ...

    @abstractmethod
    def on_exceeded_timeout_retries_error(
        self,
        client_index: int,
        error: ExceededTimeoutRetriesError,
    ):
        """Hook to execute when exceeded timeout retries.

        Args:
            client_index (int): Index of the client that executed this hook.
            error (ExceededTimeoutRetriesError): The error.
        """
        ...

    @abstractmethod
    def on_out_of_api_keys_error(
        self,
        client_index: int,
        error: OutOfAPIKeysError,
    ):
        """Hook to execute when runs out of API keys.

        Args:
            client_index (int): Index of the client that executed this hook.
            error (OutOfAPIKeysError): The error.
        """
        ...

    @abstractmethod
    def on_search_complete(
        self,
        client_index: int,
        search_string_index: int,
        results: list[SuccessResponse.Entry],
    ):
        """Hook to execute when a search is complete.

        Args:
            client_index (int): Index of the client that executed this hook.
            search_string_index (int): Index of the search string that executed this hook.
            results (list[SuccessResponse]): List with all results.
        """  # noqa: E501
        ...

    @abstractmethod
    def on_all_complete(
        self,
    ):
        """Hook to execute when every string was searched."""

    def get_available_client(
        self,
    ) -> tuple[int, ScopusClient]:
        """Verifies which client is available, and return it.

        Raises:
            NoClientsAvailableError: If all clients are being used (none is available).

        Returns:
            - the index of the client (useful for maintaining, for example, a progress bar)
            - the client itself
        """  # noqa: E501
        for i in range(len(self.clients_list)):
            if self.clients_in_use[i] is False:
                self.clients_in_use[i] = True

                return i, self.clients_list[i]

        raise NoClientsAvailableError()

    def set_client_available(
        self,
        i: int,
    ) -> None:
        """Sets the client as avaibale.

        Args:
            i (int): Index of the client to set as available.
        """
        self.clients_in_use[i] = False

    async def task_worker(
        self,
        search_string_index: int,
    ):
        """Performs the search, and executes the hooks.

        Args:
            search_string_index (int): Index of the search string to use.
        """
        client_index, client = self.get_available_client()
        search_string = self.search_strings_list[search_string_index]
        results_list: list[SuccessResponse.Entry] = list()

        self.on_search_initialize(
            client_index=client_index,
            search_string_index=search_string_index,
        )

        try:
            async for data in client.search(query=search_string):
                if isinstance(data, APIKeyExpiredResponse):
                    self.on_api_key_expired_response(
                        client_index=client_index,
                        data=data,
                    )

                elif isinstance(data, TimeoutResponse):
                    attempts_left = int(client.timeout_retries - data.timeout_retry - 1)

                    self.on_timeout_response(
                        client_index=client_index,
                        attempts_left=attempts_left,
                        search_string_index=search_string_index,
                        data=data,
                    )

                else:
                    if data.current_page == 1:
                        self.on_first_success_response(
                            client_index=client_index,
                            data=data,
                        )

                    self.on_success_response(
                        client_index=client_index,
                        data=data,
                    )

                    results_list.extend(data.entries)

        except BadRequestError as e:
            self.on_bad_request_error(
                client_index=client_index,
                search_string=search_string,
                error=e,
            )

        except PayloadTooLargeError as e:
            self.on_payload_too_large_error(
                client_index=client_index,
                search_string=search_string,
                error=e,
            )

        except ExceededTimeoutRetriesError as e:
            self.on_exceeded_timeout_retries_error(
                client_index=client_index,
                error=e,
            )

        except OutOfAPIKeysError as e:
            self.on_out_of_api_keys_error(
                client_index=client_index,
                error=e,
            )

        self.on_search_complete(
            client_index=client_index,
            results=results_list,
            search_string_index=search_string_index,
        )
        self.set_client_available(client_index)

    async def _queue_worker(
        self,
    ):
        while True:
            async with self.semaphore:
                search_string_index = await self.queue.get()
                await self.task_worker(search_string_index)
                self.queue.task_done()

    async def start(
        self,
    ):
        """Starts all of the clients."""
        self.on_all_start()

        for i in range(len(self.search_strings_list)):
            await self.queue.put(i)

        queue_workers: list[asyncio.Task] = []
        for _ in range(len(self.clients_list)):
            worker = asyncio.create_task(self._queue_worker())
            queue_workers.append(worker)

        await self.queue.join()

        for worker in queue_workers:
            worker.cancel()

        self.on_all_complete()
