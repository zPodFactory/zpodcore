from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.zpod_storage_create import ZpodStorageCreate
from ...models.zpod_storage_operation import ZpodStorageOperation
from ...types import UNSET, Response, Unset


class ZpodsStorageCreate:
    def __init__(self, client: AuthenticatedClient | Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
        *,
        body: ZpodStorageCreate,
        dry_run: bool | Unset = False,
        verbose: bool | Unset = False,
    ) -> dict[str, Any]:
        headers: dict[str, Any] = {}

        params: dict[str, Any] = {}

        params["dry_run"] = dry_run

        params["verbose"] = verbose

        params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

        _kwargs: dict[str, Any] = {
            "method": "post",
            "url": "/zpods/{id}/storages".format(
                id=quote(str(id), safe=""),
            ),
            "params": params,
        }

        _kwargs["json"] = body.to_dict()

        headers["Content-Type"] = "application/json"

        _kwargs["headers"] = headers
        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> HTTPValidationError | ZpodStorageOperation | None:
        if response.status_code == 201:
            response_201 = ZpodStorageOperation.from_dict(response.json())

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
        *,
        body: ZpodStorageCreate,
        dry_run: bool | Unset = False,
        verbose: bool | Unset = False,
    ) -> Response[HTTPValidationError | ZpodStorageOperation]:
        """zPod Storage Create

         Partition, format and mount a blank disk of the zPod as /FILER/STORAGEnn.

        Args:
            id (str):
            dry_run (bool | Unset):  Default: False.
            verbose (bool | Unset):  Default: False.
            body (ZpodStorageCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | ZpodStorageOperation]
        """

        kwargs = self._get_kwargs(
            id=id,
            body=body,
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
        *,
        body: ZpodStorageCreate,
        dry_run: bool | Unset = False,
        verbose: bool | Unset = False,
    ) -> HTTPValidationError | ZpodStorageOperation | None:
        """zPod Storage Create

         Partition, format and mount a blank disk of the zPod as /FILER/STORAGEnn.

        Args:
            id (str):
            dry_run (bool | Unset):  Default: False.
            verbose (bool | Unset):  Default: False.
            body (ZpodStorageCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | ZpodStorageOperation
        """

        return self.sync_detailed(
            id=id,
            body=body,
            dry_run=dry_run,
            verbose=verbose,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
        *,
        body: ZpodStorageCreate,
        dry_run: bool | Unset = False,
        verbose: bool | Unset = False,
    ) -> Response[HTTPValidationError | ZpodStorageOperation]:
        """zPod Storage Create

         Partition, format and mount a blank disk of the zPod as /FILER/STORAGEnn.

        Args:
            id (str):
            dry_run (bool | Unset):  Default: False.
            verbose (bool | Unset):  Default: False.
            body (ZpodStorageCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | ZpodStorageOperation]
        """

        kwargs = self._get_kwargs(
            id=id,
            body=body,
            dry_run=dry_run,
            verbose=verbose,
        )

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
        *,
        body: ZpodStorageCreate,
        dry_run: bool | Unset = False,
        verbose: bool | Unset = False,
    ) -> HTTPValidationError | ZpodStorageOperation | None:
        """zPod Storage Create

         Partition, format and mount a blank disk of the zPod as /FILER/STORAGEnn.

        Args:
            id (str):
            dry_run (bool | Unset):  Default: False.
            verbose (bool | Unset):  Default: False.
            body (ZpodStorageCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | ZpodStorageOperation
        """

        return (
            await self.asyncio_detailed(
                id=id,
                body=body,
                dry_run=dry_run,
                verbose=verbose,
            )
        ).parsed
