from http import HTTPStatus
from typing import Any, Dict, Optional, Union, cast

import httpx

from ... import errors
from ...client import Client
from ...models.http_validation_error import HTTPValidationError
from ...models.permission_group_update import PermissionGroupUpdate
from ...types import Response


class PermissionGroupsUpdate:
    def __init__(self, client: Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
        *,
        json_body: PermissionGroupUpdate,
    ) -> Dict[str, Any]:
        url = "{}/permission_groups/{id}".format(self.client.base_url, id=id)

        headers: Dict[str, str] = self.client.get_headers()
        cookies: Dict[str, Any] = self.client.get_cookies()

        json_json_body = json_body.to_dict()

        return {
            "method": "patch",
            "url": url,
            "headers": headers,
            "cookies": cookies,
            "timeout": self.client.get_timeout(),
            "follow_redirects": self.client.follow_redirects,
            "json": json_json_body,
        }

    def _parse_response(
        self, *, response: httpx.Response
    ) -> Optional[Union[Any, HTTPValidationError]]:
        if response.status_code == HTTPStatus.NO_CONTENT:
            response_204 = cast(Any, None)
            return response_204
        if response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
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
        *,
        json_body: PermissionGroupUpdate,
    ) -> Response[Union[Any, HTTPValidationError]]:
        """Update

        Args:
            id (str):
            json_body (PermissionGroupUpdate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[Any, HTTPValidationError]]
        """

        kwargs = self._get_kwargs(
            id=id,
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
        *,
        json_body: PermissionGroupUpdate,
    ) -> Optional[Union[Any, HTTPValidationError]]:
        """Update

        Args:
            id (str):
            json_body (PermissionGroupUpdate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[Any, HTTPValidationError]
        """

        return self.sync_detailed(
            id=id,
            json_body=json_body,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
        *,
        json_body: PermissionGroupUpdate,
    ) -> Response[Union[Any, HTTPValidationError]]:
        """Update

        Args:
            id (str):
            json_body (PermissionGroupUpdate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[Any, HTTPValidationError]]
        """

        kwargs = self._get_kwargs(
            id=id,
            json_body=json_body,
        )

        async with httpx.AsyncClient(verify=self.client.verify_ssl) as _client:
            response = await _client.request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
        *,
        json_body: PermissionGroupUpdate,
    ) -> Optional[Union[Any, HTTPValidationError]]:
        """Update

        Args:
            id (str):
            json_body (PermissionGroupUpdate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[Any, HTTPValidationError]
        """

        return (
            await self.asyncio_detailed(
                id=id,
                json_body=json_body,
            )
        ).parsed