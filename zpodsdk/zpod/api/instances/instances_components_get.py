from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.instance_component_view import InstanceComponentView
from ...types import Response


class InstancesComponentsGet:
    def __init__(self, client: Union[AuthenticatedClient, Client]) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
        component_id: str,
    ) -> Dict[str, Any]:
        _kwargs: Dict[str, Any] = {
            "method": "get",
            "url": "/instances/{id}/components/{component_id}".format(
                id=id,
                component_id=component_id,
            ),
        }

        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> Optional[Union[HTTPValidationError, InstanceComponentView]]:
        if response.status_code == HTTPStatus.OK:
            response_200 = InstanceComponentView.from_dict(response.json())

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
    ) -> Response[Union[HTTPValidationError, InstanceComponentView]]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        id: str,
        component_id: str,
    ) -> Response[Union[HTTPValidationError, InstanceComponentView]]:
        """Instance Component Get

        Args:
            id (str):
            component_id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, InstanceComponentView]]
        """

        kwargs = self._get_kwargs(
            id=id,
            component_id=component_id,
        )

        response = self.client.get_httpx_client().request(
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        id: str,
        component_id: str,
    ) -> Optional[Union[HTTPValidationError, InstanceComponentView]]:
        """Instance Component Get

        Args:
            id (str):
            component_id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[HTTPValidationError, InstanceComponentView]
        """

        return self.sync_detailed(
            id=id,
            component_id=component_id,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
        component_id: str,
    ) -> Response[Union[HTTPValidationError, InstanceComponentView]]:
        """Instance Component Get

        Args:
            id (str):
            component_id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, InstanceComponentView]]
        """

        kwargs = self._get_kwargs(
            id=id,
            component_id=component_id,
        )

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
        component_id: str,
    ) -> Optional[Union[HTTPValidationError, InstanceComponentView]]:
        """Instance Component Get

        Args:
            id (str):
            component_id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[HTTPValidationError, InstanceComponentView]
        """

        return (
            await self.asyncio_detailed(
                id=id,
                component_id=component_id,
            )
        ).parsed
