from http import HTTPStatus
from typing import Any, Dict, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.zpod_permission import ZpodPermission
from ...models.zpod_permission_group_add_remove import ZpodPermissionGroupAddRemove
from ...types import Response


class ZpodsPermissionsGroupsRemove:
    def __init__(self, client: Union[AuthenticatedClient, Client]) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
        permission: ZpodPermission,
        *,
        body: ZpodPermissionGroupAddRemove,
    ) -> Dict[str, Any]:
        headers: Dict[str, Any] = {}

        _kwargs: Dict[str, Any] = {
            "method": "delete",
            "url": "/zpods/{id}/permissions/{permission}/groups".format(
                id=id,
                permission=permission,
            ),
        }

        _body = body.to_dict()

        _kwargs["json"] = _body
        headers["Content-Type"] = "application/json"

        _kwargs["headers"] = headers
        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> Optional[Union[Any, HTTPValidationError]]:
        if response.status_code == HTTPStatus.NO_CONTENT:
            response_204 = cast(Any, None)
            return response_204
        if (
            response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
            and not self.client.raise_on_unexpected_status
        ):
            response_422 = HTTPValidationError.from_dict(response.json())

            return response_422
        if self.client.raise_on_unexpected_status:
            raise errors.UnexpectedStatus(response.status_code, response.content)
        else:
            return None

    def _build_response(
        self, *, response: httpx.Response
    ) -> Response[Union[Any, HTTPValidationError]]:
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
        body: ZpodPermissionGroupAddRemove,
    ) -> Response[Union[Any, HTTPValidationError]]:
        """zPod Permission Group Remove

        Args:
            id (str):
            permission (ZpodPermission):
            body (ZpodPermissionGroupAddRemove):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[Any, HTTPValidationError]]
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
        body: ZpodPermissionGroupAddRemove,
    ) -> Optional[Union[Any, HTTPValidationError]]:
        """zPod Permission Group Remove

        Args:
            id (str):
            permission (ZpodPermission):
            body (ZpodPermissionGroupAddRemove):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[Any, HTTPValidationError]
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
        body: ZpodPermissionGroupAddRemove,
    ) -> Response[Union[Any, HTTPValidationError]]:
        """zPod Permission Group Remove

        Args:
            id (str):
            permission (ZpodPermission):
            body (ZpodPermissionGroupAddRemove):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[Any, HTTPValidationError]]
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
        body: ZpodPermissionGroupAddRemove,
    ) -> Optional[Union[Any, HTTPValidationError]]:
        """zPod Permission Group Remove

        Args:
            id (str):
            permission (ZpodPermission):
            body (ZpodPermissionGroupAddRemove):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[Any, HTTPValidationError]
        """

        return (
            await self.asyncio_detailed(
                id=id,
                permission=permission,
                body=body,
            )
        ).parsed
