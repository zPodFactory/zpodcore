from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ... import errors
from ...client import Client
from ...types import Response


class RootRoot:
    def __init__(self, client: Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
    ) -> Dict[str, Any]:
        url = "{}/".format(self.client.base_url)

        headers: Dict[str, str] = self.client.get_headers()
        cookies: Dict[str, Any] = self.client.get_cookies()

        return {
            "method": "get",
            "url": url,
            "headers": headers,
            "cookies": cookies,
            "timeout": self.client.get_timeout(),
        }

    def _parse_response(self, *, response: httpx.Response) -> Optional[Any]:
        if response.status_code == HTTPStatus.OK:
            return None
        if self.client.raise_on_unexpected_status:
            raise errors.UnexpectedStatus(
                f"Unexpected status code:     {response.status_code}"
            )
        else:
            return None

    def _build_response(self, *, response: httpx.Response) -> Response[Any]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
    ) -> Response[Any]:
        """Root

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Any]
        """

        kwargs = self._get_kwargs()

        response = httpx.request(
            verify=self.client.verify_ssl,
            **kwargs,
        )

        return self._build_response(response=response)

    async def asyncio_detailed(
        self,
    ) -> Response[Any]:
        """Root

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Any]
        """

        kwargs = self._get_kwargs()

        async with httpx.AsyncClient(verify=self.client.verify_ssl) as _client:
            response = await _client.request(**kwargs)

        return self._build_response(response=response)
