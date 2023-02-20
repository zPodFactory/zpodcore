from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import Client
from ...models.component_update import ComponentUpdate
from ...models.component_view import ComponentView
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


class ComponentsUpdate:
    def __init__(self, client: Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        *,
        json_body: ComponentUpdate,
        filename: Union[Unset, None, str] = UNSET,
    ) -> Dict[str, Any]:
        url = "{}/components".format(self.client.base_url)

        headers: Dict[str, str] = self.client.get_headers()
        cookies: Dict[str, Any] = self.client.get_cookies()

        params: Dict[str, Any] = {}
        params["filename"] = filename

        params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

        json_json_body = json_body.to_dict()

        return {
            "method": "patch",
            "url": url,
            "headers": headers,
            "cookies": cookies,
            "timeout": self.client.get_timeout(),
            "json": json_json_body,
            "params": params,
        }

    def _parse_response(
        self, *, response: httpx.Response
    ) -> Optional[Union[ComponentView, HTTPValidationError]]:
        if response.status_code == HTTPStatus.CREATED:
            response_201 = ComponentView.from_dict(response.json())

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
    ) -> Response[Union[ComponentView, HTTPValidationError]]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        *,
        json_body: ComponentUpdate,
        filename: Union[Unset, None, str] = UNSET,
    ) -> Response[Union[ComponentView, HTTPValidationError]]:
        """Update

        Args:
            filename (Union[Unset, None, str]):
            json_body (ComponentUpdate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[ComponentView, HTTPValidationError]]
        """  # noqa e501

        kwargs = self._get_kwargs(
            json_body=json_body,
            filename=filename,
        )

        response = httpx.request(
            verify=self.client.verify_ssl,
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        *,
        json_body: ComponentUpdate,
        filename: Union[Unset, None, str] = UNSET,
    ) -> Optional[Union[ComponentView, HTTPValidationError]]:
        """Update

        Args:
            filename (Union[Unset, None, str]):
            json_body (ComponentUpdate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[ComponentView, HTTPValidationError]]
        """  # noqa e501

        return self.sync_detailed(
            json_body=json_body,
            filename=filename,
        ).parsed

    async def asyncio_detailed(
        self,
        *,
        json_body: ComponentUpdate,
        filename: Union[Unset, None, str] = UNSET,
    ) -> Response[Union[ComponentView, HTTPValidationError]]:
        """Update

        Args:
            filename (Union[Unset, None, str]):
            json_body (ComponentUpdate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[ComponentView, HTTPValidationError]]
        """  # noqa e501

        kwargs = self._get_kwargs(
            json_body=json_body,
            filename=filename,
        )

        async with httpx.AsyncClient(verify=self.client.verify_ssl) as _client:
            response = await _client.request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        *,
        json_body: ComponentUpdate,
        filename: Union[Unset, None, str] = UNSET,
    ) -> Optional[Union[ComponentView, HTTPValidationError]]:
        """Update

        Args:
            filename (Union[Unset, None, str]):
            json_body (ComponentUpdate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[ComponentView, HTTPValidationError]]
        """  # noqa e501

        return (
            await self.asyncio_detailed(
                json_body=json_body,
                filename=filename,
            )
        ).parsed
