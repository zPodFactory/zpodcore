from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.zpod_disk_run_view import ZpodDiskRunView
from ...types import Response


class ZpodsDiskRun:
    def __init__(self, client: AuthenticatedClient | Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
        flow_run_id: str,
    ) -> dict[str, Any]:

        _kwargs: dict[str, Any] = {
            "method": "get",
            "url": "/zpods/{id}/disks/runs/{flow_run_id}".format(
                id=quote(str(id), safe=""),
                flow_run_id=quote(str(flow_run_id), safe=""),
            ),
        }

        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> HTTPValidationError | ZpodDiskRunView | None:
        if response.status_code == 200:
            response_200 = ZpodDiskRunView.from_dict(response.json())

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
        flow_run_id: str,
    ) -> Response[HTTPValidationError | ZpodDiskRunView]:
        """zPod Disk Run

         The state of a disk add, grow or remove: the run's state and message (the
        failure when it failed) and the disk as it is now.

        Args:
            id (str):
            flow_run_id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | ZpodDiskRunView]
        """

        kwargs = self._get_kwargs(
            id=id,
            flow_run_id=flow_run_id,
        )

        response = self.client.get_httpx_client().request(
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        id: str,
        flow_run_id: str,
    ) -> HTTPValidationError | ZpodDiskRunView | None:
        """zPod Disk Run

         The state of a disk add, grow or remove: the run's state and message (the
        failure when it failed) and the disk as it is now.

        Args:
            id (str):
            flow_run_id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | ZpodDiskRunView
        """

        return self.sync_detailed(
            id=id,
            flow_run_id=flow_run_id,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
        flow_run_id: str,
    ) -> Response[HTTPValidationError | ZpodDiskRunView]:
        """zPod Disk Run

         The state of a disk add, grow or remove: the run's state and message (the
        failure when it failed) and the disk as it is now.

        Args:
            id (str):
            flow_run_id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | ZpodDiskRunView]
        """

        kwargs = self._get_kwargs(
            id=id,
            flow_run_id=flow_run_id,
        )

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
        flow_run_id: str,
    ) -> HTTPValidationError | ZpodDiskRunView | None:
        """zPod Disk Run

         The state of a disk add, grow or remove: the run's state and message (the
        failure when it failed) and the disk as it is now.

        Args:
            id (str):
            flow_run_id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | ZpodDiskRunView
        """

        return (
            await self.asyncio_detailed(
                id=id,
                flow_run_id=flow_run_id,
            )
        ).parsed
