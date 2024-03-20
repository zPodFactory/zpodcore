from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.endpoint_view_full import EndpointViewFull
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


class EndpointsGet:
    def __init__(self, client: Union[AuthenticatedClient, Client]) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
    ) -> Dict[str, Any]:
        _kwargs: Dict[str, Any] = {
            "method": "get",
            "url": "/endpoints/{id}".format(
                id=id,
            ),
        }

        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> Optional[Union[EndpointViewFull, HTTPValidationError]]:
        if response.status_code == HTTPStatus.OK:
            response_200 = EndpointViewFull.from_dict(response.json())

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
    ) -> Response[Union[EndpointViewFull, HTTPValidationError]]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        id: str,
    ) -> Response[Union[EndpointViewFull, HTTPValidationError]]:
        """Get

        Args:
            id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[EndpointViewFull, HTTPValidationError]]
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
    ) -> Optional[Union[EndpointViewFull, HTTPValidationError]]:
        """Get

        Args:
            id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[EndpointViewFull, HTTPValidationError]
        """

        return self.sync_detailed(
            id=id,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
    ) -> Response[Union[EndpointViewFull, HTTPValidationError]]:
        """Get

        Args:
            id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[EndpointViewFull, HTTPValidationError]]
        """

        kwargs = self._get_kwargs(
            id=id,
        )

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
    ) -> Optional[Union[EndpointViewFull, HTTPValidationError]]:
        """Get

        Args:
            id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[EndpointViewFull, HTTPValidationError]
        """

        return (
            await self.asyncio_detailed(
                id=id,
            )
        ).parsed
