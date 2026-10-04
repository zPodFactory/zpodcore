from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.user_update import UserUpdate
from ...models.user_update_admin import UserUpdateAdmin
from ...models.user_view_full import UserViewFull
from ...types import Response


class UsersUpdate:
    def __init__(self, client: AuthenticatedClient | Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
        *,
        body: UserUpdate | UserUpdateAdmin,
    ) -> dict[str, Any]:
        headers: dict[str, Any] = {}

        _kwargs: dict[str, Any] = {
            "method": "patch",
            "url": "/users/{id}".format(
                id=quote(str(id), safe=""),
            ),
        }

        if isinstance(body, UserUpdateAdmin):
            _kwargs["json"] = body.to_dict()
        else:
            _kwargs["json"] = body.to_dict()

        headers["Content-Type"] = "application/json"

        _kwargs["headers"] = headers
        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> HTTPValidationError | UserViewFull | None:
        if response.status_code == 201:
            response_201 = UserViewFull.from_dict(response.json())

            return response_201

        if response.status_code == 422 and not self.client.raise_on_unexpected_status:
            response_422 = HTTPValidationError.from_dict(response.json())

            return response_422

        if self.client.raise_on_unexpected_status:
            raise errors.UnexpectedStatus(response.status_code, response.content)
        else:
            return None

    def _build_response(
        self, *, response: httpx.Response
    ) -> Response[HTTPValidationError | UserViewFull]:
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
        body: UserUpdate | UserUpdateAdmin,
    ) -> Response[HTTPValidationError | UserViewFull]:
        """Update

        Args:
            id (str):
            body (UserUpdate | UserUpdateAdmin):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | UserViewFull]
        """

        kwargs = self._get_kwargs(
            id=id,
            body=body,
        )

        response = self.client.get_httpx_client().request(
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        id: str,
        *,
        body: UserUpdate | UserUpdateAdmin,
    ) -> HTTPValidationError | UserViewFull | None:
        """Update

        Args:
            id (str):
            body (UserUpdate | UserUpdateAdmin):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | UserViewFull
        """

        return self.sync_detailed(
            id=id,
            body=body,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
        *,
        body: UserUpdate | UserUpdateAdmin,
    ) -> Response[HTTPValidationError | UserViewFull]:
        """Update

        Args:
            id (str):
            body (UserUpdate | UserUpdateAdmin):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | UserViewFull]
        """

        kwargs = self._get_kwargs(
            id=id,
            body=body,
        )

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
        *,
        body: UserUpdate | UserUpdateAdmin,
    ) -> HTTPValidationError | UserViewFull | None:
        """Update

        Args:
            id (str):
            body (UserUpdate | UserUpdateAdmin):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | UserViewFull
        """

        return (
            await self.asyncio_detailed(
                id=id,
                body=body,
            )
        ).parsed
