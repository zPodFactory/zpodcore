from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.zpod_disk_run_view import ZpodDiskRunView
from ...types import Response


class ZpodsDiskRemove:
    def __init__(self, client: AuthenticatedClient | Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
        device: str,
    ) -> dict[str, Any]:

        _kwargs: dict[str, Any] = {
            "method": "delete",
            "url": "/zpods/{id}/disks/{device}".format(
                id=quote(str(id), safe=""),
                device=quote(str(device), safe=""),
            ),
        }

        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> HTTPValidationError | ZpodDiskRunView | None:
        if response.status_code == 202:
            response_202 = ZpodDiskRunView.from_dict(response.json())

            return response_202

        if response.status_code == 422 and not self.client.raise_on_unexpected_status:
            response_422 = HTTPValidationError.from_dict(response.json())

            return response_422

        if self.client.raise_on_unexpected_status:
            raise errors.UnexpectedStatus(response.status_code, response.content)
        else:
            return None

    def _build_response(
        self, *, response: httpx.Response
    ) -> Response[HTTPValidationError | ZpodDiskRunView]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        id: str,
        device: str,
    ) -> Response[HTTPValidationError | ZpodDiskRunView]:
        """zPod Disk Remove

         Remove a blank or foreign user disk with its data (refused while in use).

        Args:
            id (str):
            device (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | ZpodDiskRunView]
        """

        kwargs = self._get_kwargs(
            id=id,
            device=device,
        )

        response = self.client.get_httpx_client().request(
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        id: str,
        device: str,
    ) -> HTTPValidationError | ZpodDiskRunView | None:
        """zPod Disk Remove

         Remove a blank or foreign user disk with its data (refused while in use).

        Args:
            id (str):
            device (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | ZpodDiskRunView
        """

        return self.sync_detailed(
            id=id,
            device=device,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
        device: str,
    ) -> Response[HTTPValidationError | ZpodDiskRunView]:
        """zPod Disk Remove

         Remove a blank or foreign user disk with its data (refused while in use).

        Args:
            id (str):
            device (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | ZpodDiskRunView]
        """

        kwargs = self._get_kwargs(
            id=id,
            device=device,
        )

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
        device: str,
    ) -> HTTPValidationError | ZpodDiskRunView | None:
        """zPod Disk Remove

         Remove a blank or foreign user disk with its data (refused while in use).

        Args:
            id (str):
            device (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | ZpodDiskRunView
        """

        return (
            await self.asyncio_detailed(
                id=id,
                device=device,
            )
        ).parsed
