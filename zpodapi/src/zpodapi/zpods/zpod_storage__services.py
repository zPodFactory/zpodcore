"""Storages of a zPod's zcore: zboxapi's /storage router, checked and forwarded.

No table: a storage is what zboxapi's GET /storage reports. zpodapi checks that a
disk to format or adopt is one of this zPod's (a zpod_disks row has its serial),
so a user cannot format a disk zPodFactory did not give them.
"""

import re
from urllib.parse import quote

from fastapi import HTTPException, status

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M
from zpodcommon.enums import ZpodStorageKind

from .zpod_storage__schemas import (
    ZpodStorageAdopt,
    ZpodStorageCreate,
    ZpodStorageFolderCreate,
    ZpodStorageFolderUpdate,
)
from .zpod_zcore import STORAGE_TIMEOUT, ZcoreStorage, zcore_storage

WHAT = "a storage change"
PARTITION_RE = re.compile(r"^(sd[a-z]+)\d+$")


def q(value: str) -> str:
    return quote(value, safe="")


def with_kind(storage: dict) -> dict:
    zcore = storage.get("protected") or not storage.get("managed", True)
    kind = ZpodStorageKind.ZCORE if zcore else ZpodStorageKind.USER
    return {**storage, "kind": kind}


def operation(answer: dict) -> dict:
    if answer.get("storage"):
        answer = {**answer, "storage": with_kind(answer["storage"])}
    return answer


def flags(dry_run: bool, verbose: bool) -> dict:
    return {"dry_run": str(dry_run).lower(), "verbose": str(verbose).lower()}


class ZpodStorageService(ServiceBase):
    # ── reads ────────────────────────────────────────────────────────────────

    def get_all(self, zpod: M.Zpod) -> list[dict]:
        storages = zcore_storage(zpod, "the storage list").get("/storage")
        return [with_kind(s) for s in storages]

    def get(self, zpod: M.Zpod, name: str) -> dict:
        return with_kind(zcore_storage(zpod, "a storage").get(f"/storage/{q(name)}"))

    # ── checks ───────────────────────────────────────────────────────────────

    @staticmethod
    def refuse_foreign_disk(zcore: ZcoreStorage, zpod: M.Zpod, name: str):
        """Only a disk with a zpod_disks row of this zPod is formatted or adopted."""
        disk = zcore.get(f"/disk/{q(name)}")
        serial = M.normalise_disk_uuid(disk.get("serial"))
        if not serial or not any(d.disk_uuid == serial for d in zpod.disks):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"/dev/{name} is not one of zPod {zpod.name}'s disks "
                f"(zcli zpod disk list {zpod.name}); add one with zcli zpod disk add.",
            )

    # ── changes ──────────────────────────────────────────────────────────────

    def create(
        self, zpod: M.Zpod, item_in: ZpodStorageCreate, dry_run: bool, verbose: bool
    ) -> dict:
        zcore = zcore_storage(zpod, WHAT, STORAGE_TIMEOUT)
        disk = item_in.disk.removeprefix("/dev/")
        self.refuse_foreign_disk(zcore, zpod, disk)
        body = {"disk": disk, "lvm": item_in.lvm}
        if item_in.name:
            body["name"] = item_in.name
        return operation(
            zcore.post("/storage", json=body, params=flags(dry_run, verbose))
        )

    def adopt(
        self, zpod: M.Zpod, item_in: ZpodStorageAdopt, dry_run: bool, verbose: bool
    ) -> dict:
        zcore = zcore_storage(zpod, WHAT, STORAGE_TIMEOUT)
        device = item_in.device.removeprefix("/dev/")
        if m := PARTITION_RE.match(device):
            self.refuse_foreign_disk(zcore, zpod, m[1])
        body = {"device": device}
        if item_in.name:
            body["name"] = item_in.name
        return operation(
            zcore.post("/storage/adopt", json=body, params=flags(dry_run, verbose))
        )

    def grow(self, zpod: M.Zpod, name: str, dry_run: bool, verbose: bool) -> dict:
        zcore = zcore_storage(zpod, WHAT, STORAGE_TIMEOUT)
        return operation(
            zcore.post(f"/storage/{q(name)}/grow", params=flags(dry_run, verbose))
        )

    def delete(self, zpod: M.Zpod, name: str, dry_run: bool, verbose: bool) -> dict:
        zcore = zcore_storage(zpod, WHAT, STORAGE_TIMEOUT)
        return operation(
            zcore.delete(f"/storage/{q(name)}", params=flags(dry_run, verbose))
        )

    # ── folders ──────────────────────────────────────────────────────────────

    def folder_add(
        self, zpod: M.Zpod, name: str, folder: str, item_in: ZpodStorageFolderCreate
    ) -> dict:
        return zcore_storage(zpod, WHAT).post(
            f"/storage/{q(name)}/{q(folder)}",
            json=item_in.model_dump(exclude_none=True),
        )

    def folder_set(
        self, zpod: M.Zpod, name: str, folder: str, item_in: ZpodStorageFolderUpdate
    ) -> dict:
        return zcore_storage(zpod, WHAT, STORAGE_TIMEOUT).put(
            f"/storage/{q(name)}/{q(folder)}",
            json=item_in.model_dump(exclude_none=True),
        )

    def folder_remove(self, zpod: M.Zpod, name: str, folder: str, force: bool) -> dict:
        return zcore_storage(zpod, WHAT, STORAGE_TIMEOUT).delete(
            f"/storage/{q(name)}/{q(folder)}",
            params={"force": str(force).lower()},
        )
