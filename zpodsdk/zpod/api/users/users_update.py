from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.user_update import UserUpdate
from ...models.user_view import UserView
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    client: AuthenticatedClient,
    json_body: UserUpdate,
    username: Union[Unset, None, str] = UNSET,
    email: Union[Unset, None, str] = UNSET,
) -> Dict[str, Any]:
    url = "{}/user".format(client.base_url)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    params: Dict[str, Any] = {}
    params["username"] = username

    params["email"] = email

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    json_json_body = json_body.to_dict()

    return {
        "method": "patch",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "json": json_json_body,
        "params": params,
    }


def _parse_response(
    *, client: Client, response: httpx.Response
) -> Optional[Union[HTTPValidationError, UserView]]:
    if response.status_code == HTTPStatus.CREATED:
        response_201 = UserView.from_dict(response.json())

        return response_201
    if response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(f"Unexpected status code: {response.status_code}")
    else:
        return None


def _build_response(
    *, client: Client, response: httpx.Response
) -> Response[Union[HTTPValidationError, UserView]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    json_body: UserUpdate,
    username: Union[Unset, None, str] = UNSET,
    email: Union[Unset, None, str] = UNSET,
) -> Response[Union[HTTPValidationError, UserView]]:
    """Update

    Args:
        username (Union[Unset, None, str]):
        email (Union[Unset, None, str]):
        json_body (UserUpdate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, UserView]]
    """

    kwargs = _get_kwargs(
        client=client,
        json_body=json_body,
        username=username,
        email=email,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    json_body: UserUpdate,
    username: Union[Unset, None, str] = UNSET,
    email: Union[Unset, None, str] = UNSET,
) -> Optional[Union[HTTPValidationError, UserView]]:
    """Update

    Args:
        username (Union[Unset, None, str]):
        email (Union[Unset, None, str]):
        json_body (UserUpdate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, UserView]]
    """

    return sync_detailed(
        client=client,
        json_body=json_body,
        username=username,
        email=email,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    json_body: UserUpdate,
    username: Union[Unset, None, str] = UNSET,
    email: Union[Unset, None, str] = UNSET,
) -> Response[Union[HTTPValidationError, UserView]]:
    """Update

    Args:
        username (Union[Unset, None, str]):
        email (Union[Unset, None, str]):
        json_body (UserUpdate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, UserView]]
    """

    kwargs = _get_kwargs(
        client=client,
        json_body=json_body,
        username=username,
        email=email,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    json_body: UserUpdate,
    username: Union[Unset, None, str] = UNSET,
    email: Union[Unset, None, str] = UNSET,
) -> Optional[Union[HTTPValidationError, UserView]]:
    """Update

    Args:
        username (Union[Unset, None, str]):
        email (Union[Unset, None, str]):
        json_body (UserUpdate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, UserView]]
    """

    return (
        await asyncio_detailed(
            client=client,
            json_body=json_body,
            username=username,
            email=email,
        )
    ).parsed
