from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import Client
from ...models.endpoint_update import EndpointUpdate
from ...models.endpoint_view_full import EndpointViewFull
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


class EndpointsUpdate:
    def __init__(self, client: Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: str,
        *,
        json_body: EndpointUpdate,
    ) -> Dict[str, Any]:
        url = "{}/endpoints/{id}".format(self.client.base_url, id=id)

        headers: Dict[str, str] = self.client.get_headers()
        cookies: Dict[str, Any] = self.client.get_cookies()

        json_json_body = json_body.to_dict()

        return {
            "method": "patch",
            "url": url,
            "headers": headers,
            "cookies": cookies,
            "timeout": self.client.get_timeout(),
            "follow_redirects": self.client.follow_redirects,
            "json": json_json_body,
        }

    def _parse_response(
        self, *, response: httpx.Response
    ) -> Optional[Union[EndpointViewFull, HTTPValidationError]]:
        if response.status_code == HTTPStatus.CREATED:
            response_201 = EndpointViewFull.from_dict(response.json())

            return response_201
        if response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
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
        *,
        json_body: EndpointUpdate,
    ) -> Response[Union[EndpointViewFull, HTTPValidationError]]:
        """Update

        Args:
            id (str):
            json_body (EndpointUpdate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[EndpointViewFull, HTTPValidationError]]
        """

        kwargs = self._get_kwargs(
            id=id,
            json_body=json_body,
        )

        response = httpx.request(
            verify=self.client.verify_ssl,
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        id: str,
        *,
        json_body: EndpointUpdate,
    ) -> Optional[Union[EndpointViewFull, HTTPValidationError]]:
        """Update

        Args:
            id (str):
            json_body (EndpointUpdate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[EndpointViewFull, HTTPValidationError]
        """

        return self.sync_detailed(
            id=id,
            json_body=json_body,
        ).parsed

    async def asyncio_detailed(
        self,
        id: str,
        *,
        json_body: EndpointUpdate,
    ) -> Response[Union[EndpointViewFull, HTTPValidationError]]:
        """Update

        Args:
            id (str):
            json_body (EndpointUpdate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[EndpointViewFull, HTTPValidationError]]
        """

        kwargs = self._get_kwargs(
            id=id,
            json_body=json_body,
        )

        async with httpx.AsyncClient(verify=self.client.verify_ssl) as _client:
            response = await _client.request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: str,
        *,
        json_body: EndpointUpdate,
    ) -> Optional[Union[EndpointViewFull, HTTPValidationError]]:
        """Update

        Args:
            id (str):
            json_body (EndpointUpdate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[EndpointViewFull, HTTPValidationError]
        """

        return (
            await self.asyncio_detailed(
                id=id,
                json_body=json_body,
            )
        ).parsed
