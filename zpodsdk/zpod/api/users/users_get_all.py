from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union

import httpx

from ... import errors
from ...client import Client
from ...models.http_validation_error import HTTPValidationError
from ...models.user_view import UserView
from ...types import UNSET, Response, Unset


class UsersGetAll:
    def __init__(self, client: Client) -> None:
        self.client = client

    def _get_kwargs(
        self,
        *,
        username: Union[Unset, None, str] = UNSET,
        email: Union[Unset, None, str] = UNSET,
    ) -> Dict[str, Any]:
        url = "{}/users".format(self.client.base_url)

        headers: Dict[str, str] = self.client.get_headers()
        cookies: Dict[str, Any] = self.client.get_cookies()

        params: Dict[str, Any] = {}
        params["username"] = username

        params["email"] = email

        params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

        return {
            "method": "get",
            "url": url,
            "headers": headers,
            "cookies": cookies,
            "timeout": self.client.get_timeout(),
            "params": params,
        }

    def _parse_response(
        self, *, response: httpx.Response
    ) -> Optional[Union[HTTPValidationError, List["UserView"]]]:
        if response.status_code == HTTPStatus.OK:
            response_200 = []
            _response_200 = response.json()
            for response_200_item_data in _response_200:
                response_200_item = UserView.from_dict(response_200_item_data)

                response_200.append(response_200_item)

            return response_200
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
    ) -> Response[Union[HTTPValidationError, List["UserView"]]]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        *,
        username: Union[Unset, None, str] = UNSET,
        email: Union[Unset, None, str] = UNSET,
    ) -> Response[Union[HTTPValidationError, List["UserView"]]]:
        """Get All

        Args:
            username (Union[Unset, None, str]):
            email (Union[Unset, None, str]):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, List['UserView']]]
        """  # noqa e501

        kwargs = self._get_kwargs(
            username=username,
            email=email,
        )

        response = httpx.request(
            verify=self.client.verify_ssl,
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        *,
        username: Union[Unset, None, str] = UNSET,
        email: Union[Unset, None, str] = UNSET,
    ) -> Optional[Union[HTTPValidationError, List["UserView"]]]:
        """Get All

        Args:
            username (Union[Unset, None, str]):
            email (Union[Unset, None, str]):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, List['UserView']]]
        """  # noqa e501

        return self.sync_detailed(
            username=username,
            email=email,
        ).parsed

    async def asyncio_detailed(
        self,
        *,
        username: Union[Unset, None, str] = UNSET,
        email: Union[Unset, None, str] = UNSET,
    ) -> Response[Union[HTTPValidationError, List["UserView"]]]:
        """Get All

        Args:
            username (Union[Unset, None, str]):
            email (Union[Unset, None, str]):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, List['UserView']]]
        """  # noqa e501

        kwargs = self._get_kwargs(
            username=username,
            email=email,
        )

        async with httpx.AsyncClient(verify=self.client.verify_ssl) as _client:
            response = await _client.request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        *,
        username: Union[Unset, None, str] = UNSET,
        email: Union[Unset, None, str] = UNSET,
    ) -> Optional[Union[HTTPValidationError, List["UserView"]]]:
        """Get All

        Args:
            username (Union[Unset, None, str]):
            email (Union[Unset, None, str]):

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, List['UserView']]]
        """  # noqa e501

        return (
            await self.asyncio_detailed(
                username=username,
                email=email,
            )
        ).parsed
