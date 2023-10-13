from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union

import httpx

from ... import errors
from ...client import Client
from ...models.endpoint_permission import EndpointPermission
from ...models.endpoint_permission_group_add_remove import (
    EndpointPermissionGroupAddRemove,
)
from ...models.http_validation_error import HTTPValidationError
from ...models.user_view import UserView
from ...types import Response


class EndpointsPermissionsGroupsAdd:
    def __init__(self, client: Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
        permission: EndpointPermission,
        *,
        json_body: EndpointPermissionGroupAddRemove,
    ) -> Dict[str, Any]:
        url = "{}/endpoints/{id}/permissions/{permission}/groups".format(
            self.client.base_url, id=id, permission=permission
        )

        headers: Dict[str, str] = self.client.get_headers()
        cookies: Dict[str, Any] = self.client.get_cookies()

        json_json_body = json_body.to_dict()

        return {
            "method": "post",
            "url": url,
            "headers": headers,
            "cookies": cookies,
            "timeout": self.client.get_timeout(),
            "follow_redirects": self.client.follow_redirects,
            "json": json_json_body,
        }

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
        json_body: EndpointPermissionGroupAddRemove,
    ) -> Response[Union[HTTPValidationError, List["UserView"]]]:
        """Endpoint Permissions Group Add

        Args:
            id (str):
            permission (EndpointPermission): An enumeration.
            json_body (EndpointPermissionGroupAddRemove):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, List['UserView']]]
        """

        kwargs = self._get_kwargs(
            id=id,
            permission=permission,
            json_body=json_body,
        )

        response = httpx.request(
            verify=self.client.verify_ssl,
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        id: str,
        permission: EndpointPermission,
        *,
        json_body: EndpointPermissionGroupAddRemove,
    ) -> Optional[Union[HTTPValidationError, List["UserView"]]]:
        """Endpoint Permissions Group Add

        Args:
            id (str):
            permission (EndpointPermission): An enumeration.
            json_body (EndpointPermissionGroupAddRemove):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[HTTPValidationError, List['UserView']]
        """

        return self.sync_detailed(
            id=id,
            permission=permission,
            json_body=json_body,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
        permission: EndpointPermission,
        *,
        json_body: EndpointPermissionGroupAddRemove,
    ) -> Response[Union[HTTPValidationError, List["UserView"]]]:
        """Endpoint Permissions Group Add

        Args:
            id (str):
            permission (EndpointPermission): An enumeration.
            json_body (EndpointPermissionGroupAddRemove):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, List['UserView']]]
        """

        kwargs = self._get_kwargs(
            id=id,
            permission=permission,
            json_body=json_body,
        )

        async with httpx.AsyncClient(verify=self.client.verify_ssl) as _client:
            response = await _client.request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
        permission: EndpointPermission,
        *,
        json_body: EndpointPermissionGroupAddRemove,
    ) -> Optional[Union[HTTPValidationError, List["UserView"]]]:
        """Endpoint Permissions Group Add

        Args:
            id (str):
            permission (EndpointPermission): An enumeration.
            json_body (EndpointPermissionGroupAddRemove):

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
                json_body=json_body,
            )
        ).parsed
