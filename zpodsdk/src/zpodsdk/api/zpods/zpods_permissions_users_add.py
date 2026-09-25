from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.user_view import UserView
from ...models.zpod_permission import ZpodPermission
from ...models.zpod_permission_user_add_remove import ZpodPermissionUserAddRemove
from ...types import Response


class ZpodsPermissionsUsersAdd:
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
            "method": "post",
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
    ) -> HTTPValidationError | list[UserView] | None:
        if response.status_code == 201:
            response_201 = []
            _response_201 = response.json()
            for response_201_item_data in _response_201:
                response_201_item = UserView.from_dict(response_201_item_data)

                response_201.append(response_201_item)

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
    ) -> Response[HTTPValidationError | list[UserView]]:
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
    ) -> Response[HTTPValidationError | list[UserView]]:
        """zPod Permission User Add

        Args:
            id (str):
            permission (ZpodPermission):
            body (ZpodPermissionUserAddRemove):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | list[UserView]]
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
    ) -> HTTPValidationError | list[UserView] | None:
        """zPod Permission User Add

        Args:
            id (str):
            permission (ZpodPermission):
            body (ZpodPermissionUserAddRemove):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | list[UserView]
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
    ) -> Response[HTTPValidationError | list[UserView]]:
        """zPod Permission User Add

        Args:
            id (str):
            permission (ZpodPermission):
            body (ZpodPermissionUserAddRemove):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | list[UserView]]
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
    ) -> HTTPValidationError | list[UserView] | None:
        """zPod Permission User Add

        Args:
            id (str):
            permission (ZpodPermission):
            body (ZpodPermissionUserAddRemove):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | list[UserView]
        """

        return (
            await self.asyncio_detailed(
                id=id,
                permission=permission,
                body=body,
            )
        ).parsed
