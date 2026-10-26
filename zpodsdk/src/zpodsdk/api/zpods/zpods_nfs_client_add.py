from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.zpod_nfs_client_add import ZpodNfsClientAdd
from ...models.zpod_nfs_export_view import ZpodNfsExportView
from ...types import Response


class ZpodsNfsClientAdd:
    def __init__(self, client: AuthenticatedClient | Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
        storage: str,
        folder: str,
        *,
        body: ZpodNfsClientAdd,
    ) -> dict[str, Any]:
        headers: dict[str, Any] = {}

        _kwargs: dict[str, Any] = {
            "method": "post",
            "url": "/zpods/{id}/nfs/{storage}/{folder}/clients".format(
                id=quote(str(id), safe=""),
                storage=quote(str(storage), safe=""),
                folder=quote(str(folder), safe=""),
            ),
        }

        _kwargs["json"] = body.to_dict()

        headers["Content-Type"] = "application/json"

        _kwargs["headers"] = headers
        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> HTTPValidationError | ZpodNfsExportView | None:
        if response.status_code == 200:
            response_200 = ZpodNfsExportView.from_dict(response.json())

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
    ) -> Response[HTTPValidationError | ZpodNfsExportView]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        id: str,
        storage: str,
        folder: str,
        *,
        body: ZpodNfsClientAdd,
    ) -> Response[HTTPValidationError | ZpodNfsExportView]:
        """zPod NFS Export Client Add

        Args:
            id (str):
            storage (str):
            folder (str):
            body (ZpodNfsClientAdd):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | ZpodNfsExportView]
        """

        kwargs = self._get_kwargs(
            id=id,
            storage=storage,
            folder=folder,
            body=body,
        )

        response = self.client.get_httpx_client().request(
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        id: str,
        storage: str,
        folder: str,
        *,
        body: ZpodNfsClientAdd,
    ) -> HTTPValidationError | ZpodNfsExportView | None:
        """zPod NFS Export Client Add

        Args:
            id (str):
            storage (str):
            folder (str):
            body (ZpodNfsClientAdd):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | ZpodNfsExportView
        """

        return self.sync_detailed(
            id=id,
            storage=storage,
            folder=folder,
            body=body,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
        storage: str,
        folder: str,
        *,
        body: ZpodNfsClientAdd,
    ) -> Response[HTTPValidationError | ZpodNfsExportView]:
        """zPod NFS Export Client Add

        Args:
            id (str):
            storage (str):
            folder (str):
            body (ZpodNfsClientAdd):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | ZpodNfsExportView]
        """

        kwargs = self._get_kwargs(
            id=id,
            storage=storage,
            folder=folder,
            body=body,
        )

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
        storage: str,
        folder: str,
        *,
        body: ZpodNfsClientAdd,
    ) -> HTTPValidationError | ZpodNfsExportView | None:
        """zPod NFS Export Client Add

        Args:
            id (str):
            storage (str):
            folder (str):
            body (ZpodNfsClientAdd):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | ZpodNfsExportView
        """

        return (
            await self.asyncio_detailed(
                id=id,
                storage=storage,
                folder=folder,
                body=body,
            )
        ).parsed
