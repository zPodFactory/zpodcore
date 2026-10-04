from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.component_view_full import ComponentViewFull
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


class ComponentsGet:
    def __init__(self, client: AuthenticatedClient | Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
    ) -> dict[str, Any]:

        _kwargs: dict[str, Any] = {
            "method": "get",
            "url": "/components/{id}".format(
                id=quote(str(id), safe=""),
            ),
        }

        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> ComponentViewFull | HTTPValidationError | None:
        if response.status_code == 200:
            response_200 = ComponentViewFull.from_dict(response.json())

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
    ) -> Response[ComponentViewFull | HTTPValidationError]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        id: str,
    ) -> Response[ComponentViewFull | HTTPValidationError]:
        """Get

        Args:
            id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[ComponentViewFull | HTTPValidationError]
        """

        kwargs = self._get_kwargs(
            id=id,
        )

        response = self.client.get_httpx_client().request(
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        id: str,
    ) -> ComponentViewFull | HTTPValidationError | None:
        """Get

        Args:
            id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            ComponentViewFull | HTTPValidationError
        """

        return self.sync_detailed(
            id=id,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
    ) -> Response[ComponentViewFull | HTTPValidationError]:
        """Get

        Args:
            id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[ComponentViewFull | HTTPValidationError]
        """

        kwargs = self._get_kwargs(
            id=id,
        )

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
    ) -> ComponentViewFull | HTTPValidationError | None:
        """Get

        Args:
            id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            ComponentViewFull | HTTPValidationError
        """

        return (
            await self.asyncio_detailed(
                id=id,
            )
        ).parsed
