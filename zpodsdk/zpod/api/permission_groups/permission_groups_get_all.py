from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.permission_group_view import PermissionGroupView
from ...types import Response


class PermissionGroupsGetAll:
    def __init__(self, client: Union[AuthenticatedClient, Client]) -> None:
        self.client = client

    def _get_kwargs(
        self,
    ) -> Dict[str, Any]:
        _kwargs: Dict[str, Any] = {
            "method": "get",
            "url": "/permission_groups",
        }

        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> Optional[Union[HTTPValidationError, List["PermissionGroupView"]]]:
        if response.status_code == HTTPStatus.OK:
            response_200 = []
            _response_200 = response.json()
            for response_200_item_data in _response_200:
                response_200_item = PermissionGroupView.from_dict(
                    response_200_item_data
                )

                response_200.append(response_200_item)

            return response_200
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
    ) -> Response[Union[HTTPValidationError, List["PermissionGroupView"]]]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
    ) -> Response[Union[HTTPValidationError, List["PermissionGroupView"]]]:
        """Get All

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, List['PermissionGroupView']]]
        """

        kwargs = self._get_kwargs()

        response = self.client.get_httpx_client().request(
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
    ) -> Optional[Union[HTTPValidationError, List["PermissionGroupView"]]]:
        """Get All

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[HTTPValidationError, List['PermissionGroupView']]
        """

        return self.sync_detailed().parsed

    async def asyncio_detailed(
        self,
    ) -> Response[Union[HTTPValidationError, List["PermissionGroupView"]]]:
        """Get All

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, List['PermissionGroupView']]]
        """

        kwargs = self._get_kwargs()

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
    ) -> Optional[Union[HTTPValidationError, List["PermissionGroupView"]]]:
        """Get All

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[HTTPValidationError, List['PermissionGroupView']]
        """

        return (await self.asyncio_detailed()).parsed
