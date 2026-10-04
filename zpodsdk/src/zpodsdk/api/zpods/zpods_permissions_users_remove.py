from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.zpod_permission import ZpodPermission
from ...models.zpod_permission_user_add_remove import ZpodPermissionUserAddRemove
from ...types import Response


class ZpodsPermissionsUsersRemove:
    def __init__(self, client: AuthenticatedClient | Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
        permission: ZpodPermission,
        *,
        body: ZpodPermissionUserAddRemove,
    ) -> dict[str, Any]:
        headers: dict[str, Any] = {}

        _kwargs: dict[str, Any] = {
            "method": "delete",
            "url": "/zpods/{id}/permissions/{permission}/users".format(
                id=quote(str(id), safe=""),
                permission=quote(str(permission), safe=""),
            ),
        }

        _kwargs["json"] = body.to_dict()

        headers["Content-Type"] = "application/json"

        _kwargs["headers"] = headers
        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> Any | HTTPValidationError | None:
        if response.status_code == 204:
            response_204 = cast(Any, None)
            return response_204

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
        permission: ZpodPermission,
        *,
        body: ZpodPermissionUserAddRemove,
    ) -> Response[Any | HTTPValidationError]:
        """zPod Permission User Remove

        Args:
            id (str):
            permission (ZpodPermission):
            body (ZpodPermissionUserAddRemove):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Any | HTTPValidationError]
        """

        kwargs = self._get_kwargs(
            id=id,
            permission=permission,
            body=body,
        )

        response = self.client.get_httpx_client().request(
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        id: str,
        permission: ZpodPermission,
        *,
        body: ZpodPermissionUserAddRemove,
    ) -> Any | HTTPValidationError | None:
        """zPod Permission User Remove

        Args:
            id (str):
            permission (ZpodPermission):
            body (ZpodPermissionUserAddRemove):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Any | HTTPValidationError
        """

        return self.sync_detailed(
            id=id,
            permission=permission,
            body=body,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
        permission: ZpodPermission,
        *,
        body: ZpodPermissionUserAddRemove,
    ) -> Response[Any | HTTPValidationError]:
        """zPod Permission User Remove

        Args:
            id (str):
            permission (ZpodPermission):
            body (ZpodPermissionUserAddRemove):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Any | HTTPValidationError]
        """

        kwargs = self._get_kwargs(
            id=id,
            permission=permission,
            body=body,
        )

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
        permission: ZpodPermission,
        *,
        body: ZpodPermissionUserAddRemove,
    ) -> Any | HTTPValidationError | None:
        """zPod Permission User Remove

        Args:
            id (str):
            permission (ZpodPermission):
            body (ZpodPermissionUserAddRemove):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Any | HTTPValidationError
        """

        return (
            await self.asyncio_detailed(
                id=id,
                permission=permission,
                body=body,
            )
        ).parsed
