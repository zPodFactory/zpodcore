from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.zpod_storage_folder_removed import ZpodStorageFolderRemoved
from ...types import UNSET, Response, Unset


class ZpodsStorageFolderRemove:
    def __init__(self, client: AuthenticatedClient | Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
        name: str,
        folder: str,
        *,
        force: bool | Unset = False,
    ) -> dict[str, Any]:

        params: dict[str, Any] = {}

        params["force"] = force

        params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

        _kwargs: dict[str, Any] = {
            "method": "delete",
            "url": "/zpods/{id}/storages/{name}/folders/{folder}".format(
                id=quote(str(id), safe=""),
                name=quote(str(name), safe=""),
                folder=quote(str(folder), safe=""),
            ),
            "params": params,
        }

        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> HTTPValidationError | ZpodStorageFolderRemoved | None:
        if response.status_code == 200:
            response_200 = ZpodStorageFolderRemoved.from_dict(response.json())

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
    ) -> Response[HTTPValidationError | ZpodStorageFolderRemoved]:
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
        folder: str,
        *,
        force: bool | Unset = False,
    ) -> Response[HTTPValidationError | ZpodStorageFolderRemoved]:
        """zPod Storage Folder Remove

         Delete an unexported folder: empty, or with everything in it when force.

        Args:
            id (str):
            name (str):
            folder (str):
            force (bool | Unset):  Default: False.

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | ZpodStorageFolderRemoved]
        """

        kwargs = self._get_kwargs(
            id=id,
            name=name,
            folder=folder,
            force=force,
        )

        response = self.client.get_httpx_client().request(
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        id: str,
        name: str,
        folder: str,
        *,
        force: bool | Unset = False,
    ) -> HTTPValidationError | ZpodStorageFolderRemoved | None:
        """zPod Storage Folder Remove

         Delete an unexported folder: empty, or with everything in it when force.

        Args:
            id (str):
            name (str):
            folder (str):
            force (bool | Unset):  Default: False.

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | ZpodStorageFolderRemoved
        """

        return self.sync_detailed(
            id=id,
            name=name,
            folder=folder,
            force=force,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
        name: str,
        folder: str,
        *,
        force: bool | Unset = False,
    ) -> Response[HTTPValidationError | ZpodStorageFolderRemoved]:
        """zPod Storage Folder Remove

         Delete an unexported folder: empty, or with everything in it when force.

        Args:
            id (str):
            name (str):
            folder (str):
            force (bool | Unset):  Default: False.

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | ZpodStorageFolderRemoved]
        """

        kwargs = self._get_kwargs(
            id=id,
            name=name,
            folder=folder,
            force=force,
        )

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
        name: str,
        folder: str,
        *,
        force: bool | Unset = False,
    ) -> HTTPValidationError | ZpodStorageFolderRemoved | None:
        """zPod Storage Folder Remove

         Delete an unexported folder: empty, or with everything in it when force.

        Args:
            id (str):
            name (str):
            folder (str):
            force (bool | Unset):  Default: False.

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | ZpodStorageFolderRemoved
        """

        return (
            await self.asyncio_detailed(
                id=id,
                name=name,
                folder=folder,
                force=force,
            )
        ).parsed
