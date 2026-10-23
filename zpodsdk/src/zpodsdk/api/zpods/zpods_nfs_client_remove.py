from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.zpod_nfs_export_removed import ZpodNfsExportRemoved
from ...models.zpod_nfs_export_view import ZpodNfsExportView
from ...types import Response


class ZpodsNfsClientRemove:
    def __init__(self, client: AuthenticatedClient | Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
        storage: str,
        folder: str,
        client_path: str,
    ) -> dict[str, Any]:

        _kwargs: dict[str, Any] = {
            "method": "delete",
            "url": "/zpods/{id}/nfs/{storage}/{folder}/clients/{client_path}".format(
                id=quote(str(id), safe=""),
                storage=quote(str(storage), safe=""),
                folder=quote(str(folder), safe=""),
                client_path=quote(str(client_path), safe=""),
            ),
        }

        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> HTTPValidationError | ZpodNfsExportRemoved | ZpodNfsExportView | None:
        if response.status_code == 200:

            def _parse_response_200(
                data: object,
            ) -> ZpodNfsExportRemoved | ZpodNfsExportView:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    response_200_type_0 = ZpodNfsExportView.from_dict(data)

                    return response_200_type_0
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_1 = ZpodNfsExportRemoved.from_dict(data)

                return response_200_type_1

            response_200 = _parse_response_200(response.json())

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
    ) -> Response[HTTPValidationError | ZpodNfsExportRemoved | ZpodNfsExportView]:
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
        client_path: str,
    ) -> Response[HTTPValidationError | ZpodNfsExportRemoved | ZpodNfsExportView]:
        """zPod NFS Export Client Remove

         Remove one client; the last one removes the export (the folder stays).

        Args:
            id (str):
            storage (str):
            folder (str):
            client_path (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | ZpodNfsExportRemoved | ZpodNfsExportView]
        """

        kwargs = self._get_kwargs(
            id=id,
            storage=storage,
            folder=folder,
            client_path=client_path,
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
        client_path: str,
    ) -> HTTPValidationError | ZpodNfsExportRemoved | ZpodNfsExportView | None:
        """zPod NFS Export Client Remove

         Remove one client; the last one removes the export (the folder stays).

        Args:
            id (str):
            storage (str):
            folder (str):
            client_path (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | ZpodNfsExportRemoved | ZpodNfsExportView
        """

        return self.sync_detailed(
            id=id,
            storage=storage,
            folder=folder,
            client_path=client_path,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
        storage: str,
        folder: str,
        client_path: str,
    ) -> Response[HTTPValidationError | ZpodNfsExportRemoved | ZpodNfsExportView]:
        """zPod NFS Export Client Remove

         Remove one client; the last one removes the export (the folder stays).

        Args:
            id (str):
            storage (str):
            folder (str):
            client_path (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | ZpodNfsExportRemoved | ZpodNfsExportView]
        """

        kwargs = self._get_kwargs(
            id=id,
            storage=storage,
            folder=folder,
            client_path=client_path,
        )

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
        storage: str,
        folder: str,
        client_path: str,
    ) -> HTTPValidationError | ZpodNfsExportRemoved | ZpodNfsExportView | None:
        """zPod NFS Export Client Remove

         Remove one client; the last one removes the export (the folder stays).

        Args:
            id (str):
            storage (str):
            folder (str):
            client_path (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | ZpodNfsExportRemoved | ZpodNfsExportView
        """

        return (
            await self.asyncio_detailed(
                id=id,
                storage=storage,
                folder=folder,
                client_path=client_path,
            )
        ).parsed
