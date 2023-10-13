from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import Client
from ...models.endpoint_enet_view import EndpointENetView
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


class EndpointsEnetGet:
    def __init__(self, client: Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
        name: str,
    ) -> Dict[str, Any]:
        url = "{}/endpoints/{id}/enet/{name}".format(
            self.client.base_url, id=id, name=name
        )

        headers: Dict[str, str] = self.client.get_headers()
        cookies: Dict[str, Any] = self.client.get_cookies()

        return {
            "method": "get",
            "url": url,
            "headers": headers,
            "cookies": cookies,
            "timeout": self.client.get_timeout(),
            "follow_redirects": self.client.follow_redirects,
        }

    def _parse_response(
        self, *, response: httpx.Response
    ) -> Optional[Union[EndpointENetView, HTTPValidationError]]:
        if response.status_code == HTTPStatus.OK:
            response_200 = EndpointENetView.from_dict(response.json())

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
    ) -> Response[Union[EndpointENetView, HTTPValidationError]]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        id: str,
        name: str,
    ) -> Response[Union[EndpointENetView, HTTPValidationError]]:
        """Enet Get

        Args:
            id (str):
            name (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[EndpointENetView, HTTPValidationError]]
        """

        kwargs = self._get_kwargs(
            id=id,
            name=name,
        )

        response = httpx.request(
            verify=self.client.verify_ssl,
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        id: str,
        name: str,
    ) -> Optional[Union[EndpointENetView, HTTPValidationError]]:
        """Enet Get

        Args:
            id (str):
            name (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[EndpointENetView, HTTPValidationError]
        """

        return self.sync_detailed(
            id=id,
            name=name,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
        name: str,
    ) -> Response[Union[EndpointENetView, HTTPValidationError]]:
        """Enet Get

        Args:
            id (str):
            name (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[EndpointENetView, HTTPValidationError]]
        """

        kwargs = self._get_kwargs(
            id=id,
            name=name,
        )

        async with httpx.AsyncClient(verify=self.client.verify_ssl) as _client:
            response = await _client.request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
        name: str,
    ) -> Optional[Union[EndpointENetView, HTTPValidationError]]:
        """Enet Get

        Args:
            id (str):
            name (str):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[EndpointENetView, HTTPValidationError]
        """

        return (
            await self.asyncio_detailed(
                id=id,
                name=name,
            )
        ).parsed
