from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.zpod_network_masquerade import ZpodNetworkMasquerade
from ...models.zpod_network_view import ZpodNetworkView
from ...types import Response


class ZpodsNetworkMasquerade:
    def __init__(self, client: AuthenticatedClient | Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
        name: str,
        *,
        body: ZpodNetworkMasquerade,
    ) -> dict[str, Any]:
        headers: dict[str, Any] = {}

        _kwargs: dict[str, Any] = {
            "method": "put",
            "url": "/zpods/{id}/networks/{name}/masquerade".format(
                id=quote(str(id), safe=""),
                name=quote(str(name), safe=""),
            ),
        }

        _kwargs["json"] = body.to_dict()

        headers["Content-Type"] = "application/json"

        _kwargs["headers"] = headers
        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> HTTPValidationError | ZpodNetworkView | None:
        if response.status_code == 200:
            response_200 = ZpodNetworkView.from_dict(response.json())

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
    ) -> Response[HTTPValidationError | ZpodNetworkView]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        id: str,
        name: str,
        *,
        body: ZpodNetworkMasquerade,
    ) -> Response[HTTPValidationError | ZpodNetworkView]:
        """zPod Network Masquerade

        Args:
            id (str):
            name (str):
            body (ZpodNetworkMasquerade):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | ZpodNetworkView]
        """

        kwargs = self._get_kwargs(
            id=id,
            name=name,
            body=body,
        )

        response = self.client.get_httpx_client().request(
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        id: str,
        name: str,
        *,
        body: ZpodNetworkMasquerade,
    ) -> HTTPValidationError | ZpodNetworkView | None:
        """zPod Network Masquerade

        Args:
            id (str):
            name (str):
            body (ZpodNetworkMasquerade):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | ZpodNetworkView
        """

        return self.sync_detailed(
            id=id,
            name=name,
            body=body,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
        name: str,
        *,
        body: ZpodNetworkMasquerade,
    ) -> Response[HTTPValidationError | ZpodNetworkView]:
        """zPod Network Masquerade

        Args:
            id (str):
            name (str):
            body (ZpodNetworkMasquerade):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | ZpodNetworkView]
        """

        kwargs = self._get_kwargs(
            id=id,
            name=name,
            body=body,
        )

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
        name: str,
        *,
        body: ZpodNetworkMasquerade,
    ) -> HTTPValidationError | ZpodNetworkView | None:
        """zPod Network Masquerade

        Args:
            id (str):
            name (str):
            body (ZpodNetworkMasquerade):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | ZpodNetworkView
        """

        return (
            await self.asyncio_detailed(
                id=id,
                name=name,
                body=body,
            )
        ).parsed
