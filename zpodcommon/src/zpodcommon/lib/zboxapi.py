import json
import logging
import sys
import types

import httpx
from httpx import HTTPStatusError, RequestError  # noqa: F401

from zpodcommon import models as M
from zpodcommon.lib import database

insideFastAPI = "fastapi" in sys.modules
if insideFastAPI:
    from fastapi import HTTPException

logger = logging.getLogger(__name__)


def safejson(response: httpx.Response):
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(response.text)
        raise e
    try:
        return response.json()
    except json.JSONDecodeError:
        return {}


def safejson_fastapi(response: httpx.Response):
    try:
        return safejson(response)
    except httpx.HTTPStatusError as e:
        try:
            detail = response.json()["detail"]
        except json.JSONDecodeError:
            detail = response.text

        raise HTTPException(
            status_code=response.status_code,
            detail=detail,
        ) from e


def event_hook_request(request: httpx.Request):
    # Log Request
    print(
        f"REQUEST: {request.method.upper()} {request.url}\n"
        f"{request.content.decode()}"
    )


def event_hook_response(response: httpx.Response):
    # Add safejson to response
    response.safejson = types.MethodType(
        safejson_fastapi if insideFastAPI else safejson,
        response,
    )

    response.read()
    request = response.request

    # Log Response
    print(
        f"RESPONSE: {request.method.upper()} {request.url}\n"
        f"{response.status_code} {response.safejson() or response.text}"
    )


class ZboxApiClient(httpx.Client):
    def __init__(
        self,
        zbox_url,
        zbox_password,
        verify: bool = False,
        **kwargs,
    ):
        kwargs.setdefault("event_hooks", {})
        kwargs["event_hooks"].setdefault("request", []).insert(0, event_hook_request)
        kwargs["event_hooks"].setdefault("response", []).insert(0, event_hook_response)

        return super().__init__(
            headers={"accept": "application/json", "access_token": zbox_password},
            base_url=zbox_url,
            timeout=httpx.Timeout(30.0, connect=60.0),
            verify=verify,
            **kwargs,
        )

    @classmethod
    def by_zpod_id(
        cls,
        zpod_id: int,
        protocol="https",
        port=443,
        root_path="/zboxapi",
        **kwargs,
    ):
        with database.get_session_ctx() as session:
            zpod = session.get(M.Zpod, zpod_id)
            return cls.by_zpod(
                zpod=zpod,
                protocol=protocol,
                port=port,
                root_path=root_path,
                **kwargs,
            )

    @classmethod
    def by_zpod(
        cls,
        zpod: M.Zpod,
        protocol="https",
        port=443,
        root_path="/zboxapi",
        **kwargs,
    ):
        return cls(
            zbox_url=f"{protocol}://zbox.{zpod.domain}:{port}{root_path}",
            zbox_password=zpod.password,
            **kwargs,
        )
