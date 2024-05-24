from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.endpoint_permission import EndpointPermission
from ...models.endpoint_permission_user_add_remove import (
    EndpointPermissionUserAddRemove,
)
from ...models.http_validation_error import HTTPValidationError
from ...models.user_view import UserView
from ...types import Response


class EndpointsPermissionsUsersAdd:
    def __init__(self, client: Union[AuthenticatedClient, Client]) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
        permission: EndpointPermission,
        *,
        body: EndpointPermissionUserAddRemove,
    ) -> Dict[str, Any]:
        headers: Dict[str, Any] = {}

        _kwargs: Dict[str, Any] = {
            "method": "post",
            "url": "/endpoints/{id}/permissions/{permission}/users".format(
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
    ) -> Optional[Union[HTTPValidationError, List["UserView"]]]:
        if response.status_code == HTTPStatus.CREATED:
            response_201 = []
            _response_201 = response.json()
            for response_201_item_data in _response_201:
                response_201_item = UserView.from_dict(response_201_item_data)

                response_201.append(response_201_item)

            return response_201
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
    ) -> Response[Union[HTTPValidationError, List["UserView"]]]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        id: str,
        permission: EndpointPermission,
        *,
        body: EndpointPermissionUserAddRemove,
    ) -> Response[Union[HTTPValidationError, List["UserView"]]]:
        """Endpoint Permissions User Add

        Args:
            id (str):
            permission (EndpointPermission):
            body (EndpointPermissionUserAddRemove):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, List['UserView']]]
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
        permission: EndpointPermission,
        *,
        body: EndpointPermissionUserAddRemove,
    ) -> Optional[Union[HTTPValidationError, List["UserView"]]]:
        """Endpoint Permissions User Add

        Args:
            id (str):
            permission (EndpointPermission):
            body (EndpointPermissionUserAddRemove):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[HTTPValidationError, List['UserView']]
        """

        return self.sync_detailed(
            id=id,
            permission=permission,
            body=body,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
        permission: EndpointPermission,
        *,
        body: EndpointPermissionUserAddRemove,
    ) -> Response[Union[HTTPValidationError, List["UserView"]]]:
        """Endpoint Permissions User Add

        Args:
            id (str):
            permission (EndpointPermission):
            body (EndpointPermissionUserAddRemove):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, List['UserView']]]
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
        permission: EndpointPermission,
        *,
        body: EndpointPermissionUserAddRemove,
    ) -> Optional[Union[HTTPValidationError, List["UserView"]]]:
        """Endpoint Permissions User Add

        Args:
            id (str):
            permission (EndpointPermission):
            body (EndpointPermissionUserAddRemove):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[HTTPValidationError, List['UserView']]
        """

        return (
            await self.asyncio_detailed(
                id=id,
                permission=permission,
                body=body,
            )
        ).parsed
