from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.user_view_full import UserViewFull
from ...types import UNSET, Response, Unset


class UsersGetAll:
    def __init__(self, client: Union[AuthenticatedClient, Client]) -> None:
        self.client = client

    def _get_kwargs(
        self,
        *,
        all_: Union[Unset, bool] = False,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}

        params["all"] = all_

        params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

        _kwargs: Dict[str, Any] = {
            "method": "get",
            "url": "/users",
            "params": params,
        }

        return _kwargs

    def _parse_response(
        self, *, response: httpx.Response
    ) -> Optional[Union[HTTPValidationError, List["UserViewFull"]]]:
        if response.status_code == HTTPStatus.OK:
            response_200 = []
            _response_200 = response.json()
            for response_200_item_data in _response_200:
                response_200_item = UserViewFull.from_dict(response_200_item_data)

                response_200.append(response_200_item)

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
    ) -> Response[Union[HTTPValidationError, List["UserViewFull"]]]:
        return Response(
            status_code=HTTPStatus(response.status_code),
            content=response.content,
            headers=response.headers,
            parsed=self._parse_response(response=response),
        )

    def sync_detailed(
        self,
        *,
        all_: Union[Unset, bool] = False,
    ) -> Response[Union[HTTPValidationError, List["UserViewFull"]]]:
        """Get All

        Args:
            all_ (Union[Unset, bool]):  Default: False.

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, List['UserViewFull']]]
        """

        kwargs = self._get_kwargs(
            all_=all_,
        )

        response = self.client.get_httpx_client().request(
            **kwargs,
        )

        return self._build_response(response=response)

    def sync(
        self,
        *,
        all_: Union[Unset, bool] = False,
    ) -> Optional[Union[HTTPValidationError, List["UserViewFull"]]]:
        """Get All

        Args:
            all_ (Union[Unset, bool]):  Default: False.

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[HTTPValidationError, List['UserViewFull']]
        """

        return self.sync_detailed(
            all_=all_,
        ).parsed

    async def asyncio_detailed(
        self,
        *,
        all_: Union[Unset, bool] = False,
    ) -> Response[Union[HTTPValidationError, List["UserViewFull"]]]:
        """Get All

        Args:
            all_ (Union[Unset, bool]):  Default: False.

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Response[Union[HTTPValidationError, List['UserViewFull']]]
        """

        kwargs = self._get_kwargs(
            all_=all_,
        )

        response = await self.client.get_async_httpx_client().request(**kwargs)

        return self._build_response(response=response)

    async def asyncio(
        self,
        *,
        all_: Union[Unset, bool] = False,
    ) -> Optional[Union[HTTPValidationError, List["UserViewFull"]]]:
        """Get All

        Args:
            all_ (Union[Unset, bool]):  Default: False.

        Raises:
            errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
            httpx.TimeoutException: If the request takes longer than Client.timeout.

        Returns:
            Union[HTTPValidationError, List['UserViewFull']]
        """

        return (
            await self.asyncio_detailed(
                all_=all_,
            )
        ).parsed
