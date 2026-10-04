from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


class RootRoot:
    def __init__(self, client: AuthenticatedClient | Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
    ) -> dict[str, Any]:

        _kwargs: dict[str, Any] = {
            "method": "get",
            "url": "/",
        }

        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> HTTPValidationError | str | None:
        if response.status_code == 200:
            response_200 = response.text
            return response_200

        if response.status_code == 422 and not self.client.raise_on_unexpected_status:
            response_422 = HTTPValidationError.from_dict(response.json())

            return response_422

        if self.client.raise_on_unexpected_status:
            raise errors.UnexpectedStatus(response.status_code, response.content)
        else:
            return None

    def _build_response(
        self, *, response: httpx.Response
    ) -> Response[HTTPValidationError | str]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
    ) -> Response[HTTPValidationError | str]:
        """Root

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | str]
        """

        kwargs = self._get_kwargs()

        response = self.client.get_httpx_client().request(
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
    ) -> HTTPValidationError | str | None:
        """Root

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | str
        """

        return self.sync_detailed().parsed

    async def asyncio_detailed(
        self,
    ) -> Response[HTTPValidationError | str]:
        """Root

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | str]
        """

        kwargs = self._get_kwargs()

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
    ) -> HTTPValidationError | str | None:
        """Root

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | str
        """

        return (await self.asyncio_detailed()).parsed
