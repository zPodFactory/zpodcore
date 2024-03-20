from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.zpod_create import ZpodCreate
from ...models.zpod_view import ZpodView
from ...types import Response


class ZpodsCreate:
    def __init__(self, client: Union[AuthenticatedClient, Client]) -> None:
        self.client = client

    def _get_kwargs(
        self,
        *,
        body: ZpodCreate,
    ) -> Dict[str, Any]:
        headers: Dict[str, Any] = {}

        _kwargs: Dict[str, Any] = {
            "method": "post",
            "url": "/zpods",
        }

        _body = body.to_dict()

        _kwargs["json"] = _body
        headers["Content-Type"] = "application/json"

        _kwargs["headers"] = headers
        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> Optional[Union[HTTPValidationError, ZpodView]]:
        if response.status_code == HTTPStatus.CREATED:
            response_201 = ZpodView.from_dict(response.json())

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
    ) -> Response[Union[HTTPValidationError, ZpodView]]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        *,
        body: ZpodCreate,
    ) -> Response[Union[HTTPValidationError, ZpodView]]:
        """Create

        Args:
            body (ZpodCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, ZpodView]]
        """

        kwargs = self._get_kwargs(
            body=body,
        )

        response = self.client.get_httpx_client().request(
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        *,
        body: ZpodCreate,
    ) -> Optional[Union[HTTPValidationError, ZpodView]]:
        """Create

        Args:
            body (ZpodCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[HTTPValidationError, ZpodView]
        """

        return self.sync_detailed(
            body=body,
        ).parsed

    async def asyncio_detailed(
        self,
        *,
        body: ZpodCreate,
    ) -> Response[Union[HTTPValidationError, ZpodView]]:
        """Create

        Args:
            body (ZpodCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, ZpodView]]
        """

        kwargs = self._get_kwargs(
            body=body,
        )

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        *,
        body: ZpodCreate,
    ) -> Optional[Union[HTTPValidationError, ZpodView]]:
        """Create

        Args:
            body (ZpodCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[HTTPValidationError, ZpodView]
        """

        return (
            await self.asyncio_detailed(
                body=body,
            )
        ).parsed
