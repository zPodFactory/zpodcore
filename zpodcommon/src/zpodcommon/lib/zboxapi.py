import json
import logging
import re
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
    pass


def event_hook_response(response: httpx.Response):
    # Add safejson to response
    response.safejson = types.MethodType(
        safejson_fastapi if insideFastAPI else safejson,
        response,
    )

    response.read()


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
            zbox_url=f"{protocol}://zcore.{zpod.domain}:{port}{root_path}",
            zbox_password=zpod.password,
            **kwargs,
        )


# zcore storage capabilities (disks, storages, NFS exports) need this zboxapi: the
# /disk, /storage and /nfs routers came with 0.2.0, the disk inventory in the
# rescan answer with 0.2.1 (zcore 13.7).
ZBOXAPI_STORAGE_MIN = "0.2.1"


class ZboxApiTooOld(Exception):
    """zboxapi on a zPod's zcore is older than a feature needs."""

    def __init__(self, zpod_name: str, found: str, minimum: str):
        self.zpod_name, self.found, self.minimum = zpod_name, found, minimum
        super().__init__(
            f"zPod {zpod_name} runs zboxapi {found}; storage needs ≥ {minimum} "
            "(zcore ≥ 13.7)."
        )


def version_tuple(version: str) -> tuple[int, int, int] | None:
    """0.2.1, 0.2.1.dev3 or 0.2.1+local → (0, 2, 1); None when not a version."""
    m = re.match(r"(\d+)\.(\d+)\.(\d+)", version or "")
    return (int(m[1]), int(m[2]), int(m[3])) if m else None


def zboxapi_version(zb: httpx.Client) -> str:
    """The version zboxapi publishes in its OpenAPI document, which FastAPI serves
    without the access token. "unknown" when it does not say."""
    response = zb.get(url="/openapi.json")
    if response.status_code != 200:
        return "unknown"
    try:
        version = response.json().get("info", {}).get("version")
    except (json.JSONDecodeError, AttributeError):
        return "unknown"
    return str(version) if version else "unknown"


def require_zboxapi(
    zb: httpx.Client, zpod_name: str, minimum: str = ZBOXAPI_STORAGE_MIN
) -> str:
    """Raise ZboxApiTooOld unless zboxapi is at least `minimum`; return its version.

    Asked on every storage operation, never cached: zboxapi can be upgraded in place.
    RequestError (zcore does not answer) is left to the caller.
    """
    found = zboxapi_version(zb)
    have = version_tuple(found)
    if have is None or have < version_tuple(minimum):
        raise ZboxApiTooOld(zpod_name, found, minimum)
    return found
