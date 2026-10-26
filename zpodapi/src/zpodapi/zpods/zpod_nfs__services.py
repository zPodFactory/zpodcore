"""NFS exports of a zPod's zcore: zboxapi's /nfs router, checked and forwarded.

No table: the exports live in zcore's /etc/exports (owner system, read-only here)
and /etc/exports.d/zboxapi.exports (user-defined). zpodapi only adds the default
client list (*, D13) and the checks of zcore_storage.
"""

from urllib.parse import quote

from fastapi import Response

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M

from .zpod_nfs__schemas import ZpodNfsClientAdd, ZpodNfsCreate, ZpodNfsUpdate
from .zpod_zcore import zcore_storage

WHAT = "NFS"


def export_url(storage: str, folder: str) -> str:
    return f"/nfs/{quote(storage, safe='')}/{quote(folder, safe='')}"


class ZpodNfsService(ServiceBase):
    def get_all(self, zpod: M.Zpod) -> list[dict]:
        return zcore_storage(zpod, WHAT).get("/nfs")

    def status(self, zpod: M.Zpod) -> dict:
        return zcore_storage(zpod, WHAT).get("/nfs/status")

    def get(self, zpod: M.Zpod, storage: str, folder: str) -> dict:
        return zcore_storage(zpod, WHAT).get(export_url(storage, folder))

    def add(self, zpod: M.Zpod, export_in: ZpodNfsCreate) -> dict:
        body = {
            "storage": export_in.storage,
            "folder": export_in.folder,
            "clients": export_in.clients or ["*"],
        }
        if export_in.options:
            body["options"] = export_in.options
        return zcore_storage(zpod, WHAT).post("/nfs", json=body)

    def set(
        self,
        zpod: M.Zpod,
        storage: str,
        folder: str,
        export_in: ZpodNfsUpdate,
        response: Response,
    ) -> dict:
        body = {"clients": export_in.clients}
        if export_in.options:
            body["options"] = export_in.options
        answer = zcore_storage(zpod, WHAT).put_response(
            export_url(storage, folder), json=body
        )
        response.status_code = answer.status_code  # 201 created, 200 replaced
        return answer.safejson()

    def client_add(
        self, zpod: M.Zpod, storage: str, folder: str, client_in: ZpodNfsClientAdd
    ) -> dict:
        return zcore_storage(zpod, WHAT).post(
            f"{export_url(storage, folder)}/client",
            json={"client": client_in.client},
        )

    def client_remove(
        self, zpod: M.Zpod, storage: str, folder: str, client: str
    ) -> dict:
        # zboxapi takes the client as a path (a CIDR has a slash)
        return zcore_storage(zpod, WHAT).delete(
            f"{export_url(storage, folder)}/client/{client}"
        )

    def remove(self, zpod: M.Zpod, storage: str, folder: str) -> dict:
        return zcore_storage(zpod, WHAT).delete(export_url(storage, folder))
