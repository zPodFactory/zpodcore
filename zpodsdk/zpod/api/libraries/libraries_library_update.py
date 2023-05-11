from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import Client
from ...models.http_validation_error import HTTPValidationError
from ...models.library_view import LibraryView
from ...types import Response


class LibrariesLibraryUpdate:
    def __init__(self, client: Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
    ) -> Dict[str, Any]:
        url = "{}/libraries/{id}/update".format(self.client.base_url, id=id)

        headers: Dict[str, str] = self.client.get_headers()
        cookies: Dict[str, Any] = self.client.get_cookies()

        return {
            "method": "put",
            "url": url,
            "headers": headers,
            "cookies": cookies,
            "timeout": self.client.get_timeout(),
        }

    def _parse_response(
        self, *, response: httpx.Response
    ) -> Optional[Union[HTTPValidationError, LibraryView]]:
        if response.status_code == HTTPStatus.CREATED:
            response_201 = LibraryView.from_dict(response.json())

            return response_201
        if response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
            response_422 = HTTPValidationError.from_dict(response.json())

            return response_422
        if self.client.raise_on_unexpected_status:
            raise errors.UnexpectedStatus(
                f"Unexpected status code:     {response.status_code}"
            )
        else:
            return None

    def _build_response(
        self, *, response: httpx.Response
    ) -> Response[Union[HTTPValidationError, LibraryView]]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        id: str,
    ) -> Response[Union[HTTPValidationError, LibraryView]]:
        """Library Update

        Args:
            id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, LibraryView]]
        """  # noqa e501

        kwargs = self._get_kwargs(
            id=id,
        )

        response = httpx.request(
            verify=self.client.verify_ssl,
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        id: str,
    ) -> Optional[Union[HTTPValidationError, LibraryView]]:
        """Library Update

        Args:
            id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, LibraryView]]
        """  # noqa e501

        return self.sync_detailed(
            id=id,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
    ) -> Response[Union[HTTPValidationError, LibraryView]]:
        """Library Update

        Args:
            id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, LibraryView]]
        """  # noqa e501

        kwargs = self._get_kwargs(
            id=id,
        )

        async with httpx.AsyncClient(verify=self.client.verify_ssl) as _client:
            response = await _client.request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
    ) -> Optional[Union[HTTPValidationError, LibraryView]]:
        """Library Update

        Args:
            id (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, LibraryView]]
        """  # noqa e501

        return (
            await self.asyncio_detailed(
                id=id,
            )
        ).parsed
