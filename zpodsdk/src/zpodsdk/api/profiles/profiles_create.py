from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.profile_create import ProfileCreate
from ...models.profile_view import ProfileView
from ...types import UNSET, Response, Unset


class ProfilesCreate:
    def __init__(self, client: AuthenticatedClient | Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        *,
        body: ProfileCreate,
        force: Any | Unset = False,
    ) -> dict[str, Any]:
        headers: dict[str, Any] = {}

        params: dict[str, Any] = {}

        params["force"] = force

        params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

        _kwargs: dict[str, Any] = {
            "method": "post",
            "url": "/profiles",
            "params": params,
        }

        _kwargs["json"] = body.to_dict()

        headers["Content-Type"] = "application/json"

        _kwargs["headers"] = headers
        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> HTTPValidationError | ProfileView | None:
        if response.status_code == 201:
            response_201 = ProfileView.from_dict(response.json())

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
    ) -> Response[HTTPValidationError | ProfileView]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        *,
        body: ProfileCreate,
        force: Any | Unset = False,
    ) -> Response[HTTPValidationError | ProfileView]:
        """Create

        Args:
            force (Any | Unset):  Default: False.
            body (ProfileCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | ProfileView]
        """

        kwargs = self._get_kwargs(
            body=body,
            force=force,
        )

        response = self.client.get_httpx_client().request(
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        *,
        body: ProfileCreate,
        force: Any | Unset = False,
    ) -> HTTPValidationError | ProfileView | None:
        """Create

        Args:
            force (Any | Unset):  Default: False.
            body (ProfileCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | ProfileView
        """

        return self.sync_detailed(
            body=body,
            force=force,
        ).parsed

    async def asyncio_detailed(
        self,
        *,
        body: ProfileCreate,
        force: Any | Unset = False,
    ) -> Response[HTTPValidationError | ProfileView]:
        """Create

        Args:
            force (Any | Unset):  Default: False.
            body (ProfileCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[HTTPValidationError | ProfileView]
        """

        kwargs = self._get_kwargs(
            body=body,
            force=force,
        )

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        *,
        body: ProfileCreate,
        force: Any | Unset = False,
    ) -> HTTPValidationError | ProfileView | None:
        """Create

        Args:
            force (Any | Unset):  Default: False.
            body (ProfileCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            HTTPValidationError | ProfileView
        """

        return (
            await self.asyncio_detailed(
                body=body,
                force=force,
            )
        ).parsed
