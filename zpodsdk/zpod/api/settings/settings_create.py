from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.setting_create import SettingCreate
from ...models.setting_view import SettingView
from ...types import Response


class SettingsCreate:
    def __init__(self, client: Union[AuthenticatedClient, Client]) -> None:
        self.client = client

    def _get_kwargs(
        self,
        *,
        body: SettingCreate,
    ) -> Dict[str, Any]:
        headers: Dict[str, Any] = {}

        _kwargs: Dict[str, Any] = {
            "method": "post",
            "url": "/settings",
        }

        _body = body.to_dict()

        _kwargs["json"] = _body
        headers["Content-Type"] = "application/json"

        _kwargs["headers"] = headers
        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> Optional[Union[HTTPValidationError, SettingView]]:
        if response.status_code == HTTPStatus.CREATED:
            response_201 = SettingView.from_dict(response.json())

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
    ) -> Response[Union[HTTPValidationError, SettingView]]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        *,
        body: SettingCreate,
    ) -> Response[Union[HTTPValidationError, SettingView]]:
        """Create

        Args:
            body (SettingCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, SettingView]]
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
        body: SettingCreate,
    ) -> Optional[Union[HTTPValidationError, SettingView]]:
        """Create

        Args:
            body (SettingCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[HTTPValidationError, SettingView]
        """

        return self.sync_detailed(
            body=body,
        ).parsed

    async def asyncio_detailed(
        self,
        *,
        body: SettingCreate,
    ) -> Response[Union[HTTPValidationError, SettingView]]:
        """Create

        Args:
            body (SettingCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, SettingView]]
        """

        kwargs = self._get_kwargs(
            body=body,
        )

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        *,
        body: SettingCreate,
    ) -> Optional[Union[HTTPValidationError, SettingView]]:
        """Create

        Args:
            body (SettingCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[HTTPValidationError, SettingView]
        """

        return (
            await self.asyncio_detailed(
                body=body,
            )
        ).parsed
