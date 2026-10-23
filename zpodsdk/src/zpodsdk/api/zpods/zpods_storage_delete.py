from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.zpod_storage_operation import ZpodStorageOperation
from ...types import UNSET, Response, Unset


class ZpodsStorageDelete:
    def __init__(self, client: AuthenticatedClient | Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
        name: str,
        *,
        dry_run: bool | Unset = False,
        verbose: bool | Unset = False,
    ) -> dict[str, Any]:

        params: dict[str, Any] = {}

        params["dry_run"] = dry_run

        params["verbose"] = verbose

        params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

        _kwargs: dict[str, Any] = {
            "method": "delete",
            "url": "/zpods/{id}/storages/{name}".format(
                id=quote(str(id), safe=""),
                name=quote(str(name), safe=""),
            ),
            "params": params,
        }

        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> HTTPValidationError | ZpodStorageOperation | None:
        if response.status_code == 200:
            response_200 = ZpodStorageOperation.from_dict(response.json())

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
    ) -> Response[HTTPValidationError | ZpodStorageOperation]:
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
        dry_run: bool | Unset = False,
        verbose: bool | Unset = False,
    ) -> Response[HTTPValidationError | ZpodStorageOperation]:
        """zPod Storage Delete

         Unmount and forget the mount unit; the filesystem stays on the disk (409
        while it has exports).

        Args:
            id (str):
            name (str):
            dry_run (bool | Unset):  Default: False.
            verbose (bool | Unset):  Default: False.

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | ZpodStorageOperation]
        """

        kwargs = self._get_kwargs(
            id=id,
            name=name,
            dry_run=dry_run,
            verbose=verbose,
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
        dry_run: bool | Unset = False,
        verbose: bool | Unset = False,
    ) -> HTTPValidationError | ZpodStorageOperation | None:
        """zPod Storage Delete

         Unmount and forget the mount unit; the filesystem stays on the disk (409
        while it has exports).

        Args:
            id (str):
            name (str):
            dry_run (bool | Unset):  Default: False.
            verbose (bool | Unset):  Default: False.

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | ZpodStorageOperation
        """

        return self.sync_detailed(
            id=id,
            name=name,
            dry_run=dry_run,
            verbose=verbose,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
        name: str,
        *,
        dry_run: bool | Unset = False,
        verbose: bool | Unset = False,
    ) -> Response[HTTPValidationError | ZpodStorageOperation]:
        """zPod Storage Delete

         Unmount and forget the mount unit; the filesystem stays on the disk (409
        while it has exports).

        Args:
            id (str):
            name (str):
            dry_run (bool | Unset):  Default: False.
            verbose (bool | Unset):  Default: False.

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | ZpodStorageOperation]
        """

        kwargs = self._get_kwargs(
            id=id,
            name=name,
            dry_run=dry_run,
            verbose=verbose,
        )

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
        name: str,
        *,
        dry_run: bool | Unset = False,
        verbose: bool | Unset = False,
    ) -> HTTPValidationError | ZpodStorageOperation | None:
        """zPod Storage Delete

         Unmount and forget the mount unit; the filesystem stays on the disk (409
        while it has exports).

        Args:
            id (str):
            name (str):
            dry_run (bool | Unset):  Default: False.
            verbose (bool | Unset):  Default: False.

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | ZpodStorageOperation
        """

        return (
            await self.asyncio_detailed(
                id=id,
                name=name,
                dry_run=dry_run,
                verbose=verbose,
            )
        ).parsed
