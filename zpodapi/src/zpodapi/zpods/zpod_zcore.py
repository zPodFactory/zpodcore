"""zboxapi on a zPod's zcore, as the zcore storage capabilities use it.

Disks, storages and NFS exports all go through ``zcore_storage(zpod, what)``: it
refuses before anything is sent when zcore is not ACTIVE (409), when its zboxapi is
older than ZBOXAPI_STORAGE_MIN (501) and when it does not answer (503). zboxapi's
own refusals (400, 403, 404, 409, 422) come back unchanged.
"""

import httpx
from fastapi import HTTPException, status

from zpodcommon import models as M
from zpodcommon.lib.zboxapi import (
    RequestError,
    ZboxApiClient,
    ZboxApiTooOld,
    require_zboxapi,
)

from .zpod_network__services import ZpodNetworkService

# exportfs and folder changes answer in well under a second; mkfs on a large disk,
# growpart and resize2fs take longer.
NFS_TIMEOUT = httpx.Timeout(60.0, connect=10.0)
STORAGE_TIMEOUT = httpx.Timeout(300.0, connect=10.0)


def unreachable(zpod: M.Zpod, e: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"zcore.{zpod.domain} does not answer: {e}",
    )


class ZcoreStorage:
    """The calls of one request to zboxapi; every answer goes through safejson, so
    zboxapi's errors become the same HTTPException for the caller."""

    def __init__(self, zpod: M.Zpod, zb: ZboxApiClient):
        self.zpod, self.zb = zpod, zb

    def _call(self, method: str, url: str, **kwargs):
        try:
            response = getattr(self.zb, method)(url=url, **kwargs)
        except RequestError as e:
            raise unreachable(self.zpod, e) from e
        return response

    def get(self, url: str, **kwargs):
        return self._call("get", url, **kwargs).safejson()

    def post(self, url: str, **kwargs):
        return self._call("post", url, **kwargs).safejson()

    def put_response(self, url: str, **kwargs):
        """PUT, answering the response itself: its status code tells created (201)
        from replaced (200)."""
        response = self._call("put", url, **kwargs)
        response.safejson()
        return response

    def put(self, url: str, **kwargs):
        return self.put_response(url, **kwargs).safejson()

    def delete(self, url: str, **kwargs):
        return self._call("delete", url, **kwargs).safejson()


def zcore_storage(
    zpod: M.Zpod, what: str, timeout: httpx.Timeout = NFS_TIMEOUT
) -> ZcoreStorage:
    """zboxapi of this zPod, checked for the storage capabilities (D19)."""
    if not ZpodNetworkService.zcore_ready(zpod):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"zcore of zPod {zpod.name} is not ACTIVE (zPod {zpod.status}); "
                f"{what} needs a running zcore."
            ),
        )
    try:
        zb = ZboxApiClient.by_zpod(zpod)
        zb.timeout = timeout  # the client sets its own; override after
        require_zboxapi(zb, zpod.name)
    except ZboxApiTooOld as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e)
        ) from e
    except RequestError as e:
        raise unreachable(zpod, e) from e
    return ZcoreStorage(zpod, zb)
