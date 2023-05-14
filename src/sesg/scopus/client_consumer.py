"""Scopus Client Consumer module.

This module provides an Abstract class with an implementation of the
[`ScopusClient.search`][sesg.scopus.ScopusClient.search] function, in addition to some useful hooks.
"""  # noqa: E501

from abc import ABC, abstractmethod

from .api import BadRequestError, PayloadTooLargeError, SuccessResponse
from .client import (
    APIKeyExpiredResponse,
    ExceededTimeoutRetriesError,
    OutOfAPIKeysError,
    ScopusClient,
    TimeoutResponse,
)


class BaseScopusClientConsumer(ABC):
    """Base abstract class that provides hooks for each possible outcome of the execution of the [`ScopusClient.search`][sesg.scopus.ScopusClient.search] function.

    Attributes:
        client (ScopusClient): The scopus client that will execute the search.
    """  # noqa: E501

    __client: ScopusClient

    def __init__(
        self,
        *,
        client: ScopusClient,
    ) -> None:
        """Creates a ScopusClientConsumerInstance.

        Args:
            client (ScopusClient): The scopus client that will execute the search.
        """
        self.__client = client

    @property
    def client(self) -> ScopusClient:
        """The client that was used to create this instance."""
        return self.__client

    @abstractmethod
    def on_api_key_expired_response(
        self,
        data: APIKeyExpiredResponse,
    ):
        """Hook to execute when the response indicates an expired API key.

        Args:
            data (APIKeyExpiredResponse): The response.
        """  # noqa: E501
        ...

    @abstractmethod
    def on_timeout_response(
        self,
        data: TimeoutResponse,
    ):
        """Hook to execute when the request timed out.

        Args:
            data (TimeoutResponse): The response.
        """
        ...

    @abstractmethod
    def on_first_success_response(
        self,
        data: SuccessResponse,
    ):
        """Hook to execute when receives a successfull response for the first time.

        Notice that this hook is executed before
        [`on_success_response`][sesg.scopus.BaseScopusClientConsumer.on_success_response],
        meaning that on the first success, both of these hooks will be executed.

        Args:
            data (SuccessResponse): The response.
        """  # noqa: E501
        ...

    @abstractmethod
    def on_success_response(
        self,
        data: SuccessResponse,
    ):
        """Hook to execute when the response is successfull.

        Args:
            data (SuccessResponse): The response.
        """
        ...

    @abstractmethod
    def on_bad_request_error(
        self,
        error: BadRequestError,
    ):
        """Hook to execute when a bad request occurs.

        Args:
            error (BadRequestError): The error.
        """
        ...

    @abstractmethod
    def on_payload_too_large_error(
        self,
        error: PayloadTooLargeError,
    ):
        """Hook to execute when the payload is too large.

        Args:
            error (PayloadTooLargeError): The error.
        """
        ...

    @abstractmethod
    def on_exceeded_timeout_retries_error(
        self,
        error: ExceededTimeoutRetriesError,
    ):
        """Hook to execute when exceeded timeout retries.

        Args:
            error (ExceededTimeoutRetriesError): The error.
        """
        ...

    @abstractmethod
    def on_out_of_api_keys_error(
        self,
        error: OutOfAPIKeysError,
    ):
        """Hook to execute when runs out of API keys.

        Args:
            error (OutOfAPIKeysError): The error.
        """
        ...

    @abstractmethod
    def on_search_finalization(
        self,
        results: list[SuccessResponse],
    ):
        """Hook to execute when the search is finalized.

        Args:
            results (list[SuccessResponse]): List with all results.
        """
        ...

    async def search(
        self,
        query: str,
    ) -> None:
        """Executes the search and the hooks when required.

        Args:
            query (str): The string to search.

        Raises:
            BadRequestError: When the client raises a BadRequestError.
            PayloadTooLargeError: When the client raises a PayloadTooLargeError.
            ExceededTimeoutRetriesError: When the client raises a ExceededTimeoutRetriesError.
            OutOfAPIKeysError: When the client raises a OutOfAPIKeysError.

        Returns:
            A list with all of the results for this query.
        """  # noqa: E501
        results: list[SuccessResponse] = list()

        try:
            async for data in self.client.search(query):
                if isinstance(data, APIKeyExpiredResponse):
                    self.on_api_key_expired_response(data)

                elif isinstance(data, TimeoutResponse):
                    self.on_timeout_response(data)

                else:
                    if data.current_page == 1:
                        self.on_first_success_response(data)

                    self.on_success_response(data)
                    results.append(data)

            self.on_search_finalization(results)

        except BadRequestError as e:
            self.on_bad_request_error(e)
            raise e

        except PayloadTooLargeError as e:
            self.on_payload_too_large_error(e)
            raise e

        except ExceededTimeoutRetriesError as e:
            self.on_exceeded_timeout_retries_error(e)
            raise e

        except OutOfAPIKeysError as e:
            self.on_out_of_api_keys_error(e)
            raise e
