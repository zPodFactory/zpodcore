from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.zpod_dns_update import ZpodDnsUpdate
from ...types import Response


class ZpodsDnsUpdate:
    def __init__(self, client: AuthenticatedClient | Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
        ip: str,
        hostname: str,
        *,
        body: ZpodDnsUpdate,
    ) -> dict[str, Any]:
        headers: dict[str, Any] = {}

        _kwargs: dict[str, Any] = {
            "method": "put",
            "url": "/zpods/{id}/dns/{ip}/{hostname}".format(
                id=quote(str(id), safe=""),
                ip=quote(str(ip), safe=""),
                hostname=quote(str(hostname), safe=""),
            ),
        }

        _kwargs["json"] = body.to_dict()

        headers["Content-Type"] = "application/json"

        _kwargs["headers"] = headers
        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> Any | HTTPValidationError | None:
        if response.status_code == 201:
            response_201 = response.json()
            return response_201

        if response.status_code == 422 and not self.client.raise_on_unexpected_status:
            response_422 = HTTPValidationError.from_dict(response.json())

            return response_422

        if self.client.raise_on_unexpected_status:
            raise errors.UnexpectedStatus(response.status_code, response.content)
        else:
            return None

    def _build_response(
        self, *, response: httpx.Response
    ) -> Response[Any | HTTPValidationError]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        id: str,
        ip: str,
        hostname: str,
        *,
        body: ZpodDnsUpdate,
    ) -> Response[Any | HTTPValidationError]:
        """zPod Dns Update

        Args:
            id (str):
            ip (str):
            hostname (str):
            body (ZpodDnsUpdate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Any | HTTPValidationError]
        """

        kwargs = self._get_kwargs(
            id=id,
            ip=ip,
            hostname=hostname,
            body=body,
        )

        response = self.client.get_httpx_client().request(
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        id: str,
        ip: str,
        hostname: str,
        *,
        body: ZpodDnsUpdate,
    ) -> Any | HTTPValidationError | None:
        """zPod Dns Update

        Args:
            id (str):
            ip (str):
            hostname (str):
            body (ZpodDnsUpdate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Any | HTTPValidationError
        """

        return self.sync_detailed(
            id=id,
            ip=ip,
            hostname=hostname,
            body=body,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
        ip: str,
        hostname: str,
        *,
        body: ZpodDnsUpdate,
    ) -> Response[Any | HTTPValidationError]:
        """zPod Dns Update

        Args:
            id (str):
            ip (str):
            hostname (str):
            body (ZpodDnsUpdate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Any | HTTPValidationError]
        """

        kwargs = self._get_kwargs(
            id=id,
            ip=ip,
            hostname=hostname,
            body=body,
        )

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
        ip: str,
        hostname: str,
        *,
        body: ZpodDnsUpdate,
    ) -> Any | HTTPValidationError | None:
        """zPod Dns Update

        Args:
            id (str):
            ip (str):
            hostname (str):
            body (ZpodDnsUpdate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Any | HTTPValidationError
        """

        return (
            await self.asyncio_detailed(
                id=id,
                ip=ip,
                hostname=hostname,
                body=body,
            )
        ).parsed
