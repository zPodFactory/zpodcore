from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import Client
from ...models.http_validation_error import HTTPValidationError
from ...models.instance_component_create import InstanceComponentCreate
from ...models.instance_component_view import InstanceComponentView
from ...types import Response


class InstancesComponentsCreate:
    def __init__(self, client: Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        id: int,
        *,
        json_body: InstanceComponentCreate,
    ) -> Dict[str, Any]:
        url = "{}/instances/{id}/components".format(self.client.base_url, id=id)

        headers: Dict[str, str] = self.client.get_headers()
        cookies: Dict[str, Any] = self.client.get_cookies()

        json_json_body = json_body.to_dict()

        return {
            "method": "post",
            "url": url,
            "headers": headers,
            "cookies": cookies,
            "timeout": self.client.get_timeout(),
            "json": json_json_body,
        }

    def _parse_response(
        self, *, response: httpx.Response
    ) -> Optional[Union[HTTPValidationError, InstanceComponentView]]:
        if response.status_code == HTTPStatus.CREATED:
            response_201 = InstanceComponentView.from_dict(response.json())

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
    ) -> Response[Union[HTTPValidationError, InstanceComponentView]]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        id: int,
        *,
        json_body: InstanceComponentCreate,
    ) -> Response[Union[HTTPValidationError, InstanceComponentView]]:
        """Components Create

        Args:
            id (int):
            json_body (InstanceComponentCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, InstanceComponentView]]
        """  # noqa e501

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
        id: int,
        *,
        json_body: InstanceComponentCreate,
    ) -> Optional[Union[HTTPValidationError, InstanceComponentView]]:
        """Components Create

        Args:
            id (int):
            json_body (InstanceComponentCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, InstanceComponentView]]
        """  # noqa e501

        return self.sync_detailed(
            id=id,
            json_body=json_body,
        ).parsed

    async def asyncio_detailed(
        self,
        id: int,
        *,
        json_body: InstanceComponentCreate,
    ) -> Response[Union[HTTPValidationError, InstanceComponentView]]:
        """Components Create

        Args:
            id (int):
            json_body (InstanceComponentCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, InstanceComponentView]]
        """  # noqa e501

        kwargs = self._get_kwargs(
            id=id,
            json_body=json_body,
        )

        async with httpx.AsyncClient(verify=self.client.verify_ssl) as _client:
            response = await _client.request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        id: int,
        *,
        json_body: InstanceComponentCreate,
    ) -> Optional[Union[HTTPValidationError, InstanceComponentView]]:
        """Components Create

        Args:
            id (int):
            json_body (InstanceComponentCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, InstanceComponentView]]
        """  # noqa e501

        return (
            await self.asyncio_detailed(
                id=id,
                json_body=json_body,
            )
        ).parsed