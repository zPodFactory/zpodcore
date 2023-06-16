from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import Client
from ...models.http_validation_error import HTTPValidationError
from ...models.profile_create import ProfileCreate
from ...models.profile_view import ProfileView
from ...types import UNSET, Response, Unset


class ProfilesCreate:
    def __init__(self, client: Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        *,
        json_body: ProfileCreate,
        force: Union[Unset, None, Any] = UNSET,
    ) -> Dict[str, Any]:
        url = "{}/profiles".format(self.client.base_url)

        headers: Dict[str, str] = self.client.get_headers()
        cookies: Dict[str, Any] = self.client.get_cookies()

        params: Dict[str, Any] = {}
        params["force"] = force

        params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

        json_json_body = json_body.to_dict()

        return {
            "method": "post",
            "url": url,
            "headers": headers,
            "cookies": cookies,
            "timeout": self.client.get_timeout(),
            "follow_redirects": self.client.follow_redirects,
            "json": json_json_body,
            "params": params,
        }

    def _parse_response(
        self, *, response: httpx.Response
    ) -> Optional[Union[HTTPValidationError, ProfileView]]:
        if response.status_code == HTTPStatus.CREATED:
            response_201 = ProfileView.from_dict(response.json())

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
    ) -> Response[Union[HTTPValidationError, ProfileView]]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        *,
        json_body: ProfileCreate,
        force: Union[Unset, None, Any] = UNSET,
    ) -> Response[Union[HTTPValidationError, ProfileView]]:
        """Create

        Args:
            force (Union[Unset, None, Any]):
            json_body (ProfileCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, ProfileView]]
        """

        kwargs = self._get_kwargs(
            json_body=json_body,
            force=force,
        )

        response = httpx.request(
            verify=self.client.verify_ssl,
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        *,
        json_body: ProfileCreate,
        force: Union[Unset, None, Any] = UNSET,
    ) -> Optional[Union[HTTPValidationError, ProfileView]]:
        """Create

        Args:
            force (Union[Unset, None, Any]):
            json_body (ProfileCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[HTTPValidationError, ProfileView]
        """

        return self.sync_detailed(
            json_body=json_body,
            force=force,
        ).parsed

    async def asyncio_detailed(
        self,
        *,
        json_body: ProfileCreate,
        force: Union[Unset, None, Any] = UNSET,
    ) -> Response[Union[HTTPValidationError, ProfileView]]:
        """Create

        Args:
            force (Union[Unset, None, Any]):
            json_body (ProfileCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, ProfileView]]
        """

        kwargs = self._get_kwargs(
            json_body=json_body,
            force=force,
        )

        async with httpx.AsyncClient(verify=self.client.verify_ssl) as _client:
            response = await _client.request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        *,
        json_body: ProfileCreate,
        force: Union[Unset, None, Any] = UNSET,
    ) -> Optional[Union[HTTPValidationError, ProfileView]]:
        """Create

        Args:
            force (Union[Unset, None, Any]):
            json_body (ProfileCreate):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[HTTPValidationError, ProfileView]
        """

        return (
            await self.asyncio_detailed(
                json_body=json_body,
                force=force,
            )
        ).parsed
