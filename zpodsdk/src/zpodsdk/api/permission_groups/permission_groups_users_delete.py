from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


class PermissionGroupsUsersDelete:
    def __init__(self, client: AuthenticatedClient | Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
        user_id: int,
    ) -> dict[str, Any]:

        _kwargs: dict[str, Any] = {
            "method": "delete",
            "url": "/permission_groups/{id}/users/{user_id}".format(
                id=quote(str(id), safe=""),
                user_id=quote(str(user_id), safe=""),
            ),
        }

        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> Any | HTTPValidationError | None:
        if response.status_code == 204:
            response_204 = cast(Any, None)
            return response_204

        if response.status_code == 422 and not self.client.raise_on_unexpected_status:
            response_422 = HTTPValidationError.from_dict(response.json())

            return response_422

        if self.client.raise_on_unexpected_status:
            raise errors.UnexpectedStatus(response.status_code, response.content)
        else:
            return None

    def _build_response(
        self, *, response: httpx.Response
    ) -> Response[Any | HTTPValidationError]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        id: str,
        user_id: int,
    ) -> Response[Any | HTTPValidationError]:
        """Permission Group User Delete

        Args:
            id (str):
            user_id (int):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Any | HTTPValidationError]
        """

        kwargs = self._get_kwargs(
            id=id,
            user_id=user_id,
        )

        response = self.client.get_httpx_client().request(
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        id: str,
        user_id: int,
    ) -> Any | HTTPValidationError | None:
        """Permission Group User Delete

        Args:
            id (str):
            user_id (int):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Any | HTTPValidationError
        """

        return self.sync_detailed(
            id=id,
            user_id=user_id,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
        user_id: int,
    ) -> Response[Any | HTTPValidationError]:
        """Permission Group User Delete

        Args:
            id (str):
            user_id (int):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Any | HTTPValidationError]
        """

        kwargs = self._get_kwargs(
            id=id,
            user_id=user_id,
        )

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
        user_id: int,
    ) -> Any | HTTPValidationError | None:
        """Permission Group User Delete

        Args:
            id (str):
            user_id (int):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Any | HTTPValidationError
        """

        return (
            await self.asyncio_detailed(
                id=id,
                user_id=user_id,
            )
        ).parsed
