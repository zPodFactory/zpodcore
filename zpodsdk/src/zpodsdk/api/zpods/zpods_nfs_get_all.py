from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.zpod_nfs_export_view import ZpodNfsExportView
from ...types import Response


class ZpodsNfsGetAll:
    def __init__(self, client: AuthenticatedClient | Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
    ) -> dict[str, Any]:

        _kwargs: dict[str, Any] = {
            "method": "get",
            "url": "/zpods/{id}/nfs".format(
                id=quote(str(id), safe=""),
            ),
        }

        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> HTTPValidationError | list[ZpodNfsExportView] | None:
        if response.status_code == 200:
            response_200 = []
            _response_200 = response.json()
            for response_200_item_data in _response_200:
                response_200_item = ZpodNfsExportView.from_dict(response_200_item_data)

                response_200.append(response_200_item)

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
    ) -> Response[HTTPValidationError | list[ZpodNfsExportView]]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        id: str,
    ) -> Response[HTTPValidationError | list[ZpodNfsExportView]]:
        """zPod NFS Export Get All

         Every export of zcore: /etc/exports (owner system) and the user-defined ones.

        Args:
            id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | list[ZpodNfsExportView]]
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
    ) -> HTTPValidationError | list[ZpodNfsExportView] | None:
        """zPod NFS Export Get All

         Every export of zcore: /etc/exports (owner system) and the user-defined ones.

        Args:
            id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | list[ZpodNfsExportView]
        """

        return self.sync_detailed(
            id=id,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
    ) -> Response[HTTPValidationError | list[ZpodNfsExportView]]:
        """zPod NFS Export Get All

         Every export of zcore: /etc/exports (owner system) and the user-defined ones.

        Args:
            id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | list[ZpodNfsExportView]]
        """

        kwargs = self._get_kwargs(
            id=id,
        )

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
    ) -> HTTPValidationError | list[ZpodNfsExportView] | None:
        """zPod NFS Export Get All

         Every export of zcore: /etc/exports (owner system) and the user-defined ones.

        Args:
            id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | list[ZpodNfsExportView]
        """

        return (
            await self.asyncio_detailed(
                id=id,
            )
        ).parsed
