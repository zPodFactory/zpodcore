from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


class RootRoot:
    def __init__(self, client: Union[AuthenticatedClient, Client]) -> None:
        self.client = client

    def _get_kwargs(
        self,
    ) -> Dict[str, Any]:
        _kwargs: Dict[str, Any] = {
            "method": "get",
            "url": "/",
        }

        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> Optional[Union[Any, HTTPValidationError]]:
        if response.status_code == HTTPStatus.OK:
            response_200 = response.json()
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
    ) -> Response[Union[Any, HTTPValidationError]]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
    ) -> Response[Union[Any, HTTPValidationError]]:
        """Root

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[Any, HTTPValidationError]]
        """

        kwargs = self._get_kwargs()

        response = self.client.get_httpx_client().request(
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
    ) -> Optional[Union[Any, HTTPValidationError]]:
        """Root

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[Any, HTTPValidationError]
        """

        return self.sync_detailed().parsed

    async def asyncio_detailed(
        self,
    ) -> Response[Union[Any, HTTPValidationError]]:
        """Root

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[Any, HTTPValidationError]]
        """

        kwargs = self._get_kwargs()

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
    ) -> Optional[Union[Any, HTTPValidationError]]:
        """Root

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[Any, HTTPValidationError]
        """

        return (await self.asyncio_detailed()).parsed
