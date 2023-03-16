from http import HTTPStatus
from typing import Any, Dict, Optional, Union, cast

import httpx

from ... import errors
from ...client import Client
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


class InstancesComponentsDelete:
    def __init__(self, client: Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: int,
        component_uid: str,
    ) -> Dict[str, Any]:
        url = "{}/instances/{id}/components/{component_uid}".format(
            self.client.base_url, id=id, component_uid=component_uid
        )

        headers: Dict[str, str] = self.client.get_headers()
        cookies: Dict[str, Any] = self.client.get_cookies()

        return {
            "method": "delete",
            "url": url,
            "headers": headers,
            "cookies": cookies,
            "timeout": self.client.get_timeout(),
        }

    def _parse_response(
        self, *, response: httpx.Response
    ) -> Optional[Union[Any, HTTPValidationError]]:
        if response.status_code == HTTPStatus.NO_CONTENT:
            response_204 = cast(Any, None)
            return response_204
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
    ) -> Response[Union[Any, HTTPValidationError]]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        id: int,
        component_uid: str,
    ) -> Response[Union[Any, HTTPValidationError]]:
        """Components Delete

        Args:
            id (int):
            component_uid (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[Any, HTTPValidationError]]
        """  # noqa e501

        kwargs = self._get_kwargs(
            id=id,
            component_uid=component_uid,
        )

        response = httpx.request(
            verify=self.client.verify_ssl,
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        id: int,
        component_uid: str,
    ) -> Optional[Union[Any, HTTPValidationError]]:
        """Components Delete

        Args:
            id (int):
            component_uid (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[Any, HTTPValidationError]]
        """  # noqa e501

        return self.sync_detailed(
            id=id,
            component_uid=component_uid,
        ).parsed

    async def asyncio_detailed(
        self,
        id: int,
        component_uid: str,
    ) -> Response[Union[Any, HTTPValidationError]]:
        """Components Delete

        Args:
            id (int):
            component_uid (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[Any, HTTPValidationError]]
        """  # noqa e501

        kwargs = self._get_kwargs(
            id=id,
            component_uid=component_uid,
        )

        async with httpx.AsyncClient(verify=self.client.verify_ssl) as _client:
            response = await _client.request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: int,
        component_uid: str,
    ) -> Optional[Union[Any, HTTPValidationError]]:
        """Components Delete

        Args:
            id (int):
            component_uid (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[Any, HTTPValidationError]]
        """  # noqa e501

        return (
            await self.asyncio_detailed(
                id=id,
                component_uid=component_uid,
            )
        ).parsed
