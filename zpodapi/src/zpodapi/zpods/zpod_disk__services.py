"""Virtual disks of a zPod's zcore VM: rows in zpod_disks, Prefect flows for every
change, zboxapi for what zcore sees.

A row holds the vSphere handles; the device name and what is on the disk are read
from zboxapi on every list and matched by serial = the row's disk_uuid. A change
sets the row PENDING (one per zPod) and starts zpod_disk_add, _grow or _remove;
the CLI follows the run.
"""

import re

from fastapi import HTTPException, status

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M
from zpodcommon.enums import ZpodDiskKind, ZpodDiskStatus
from zpodcommon.lib.dbutils import DBUtils
from zpodcommon.lib.zpodengine_client import ZpodEngineClient

from .zpod_disk__schemas import ZpodDiskView
from .zpod_zcore import zcore_storage

GIB = 1024**3
DEFAULT_DISK_MAX_GB = 2048
REMOVABLE = ("blank", "foreign")
WHAT = "a disk change"


def device_name(device: str) -> str:
    """sdc, /dev/sdc → sdc."""
    return device.removeprefix("/dev/")


class ZpodDiskService(ServiceBase):
    base_model: M.ZpodDisk = M.ZpodDisk

    # ── reads ────────────────────────────────────────────────────────────────

    @staticmethod
    def live(zpod: M.Zpod) -> list[dict] | None:
        """zboxapi's GET /disk; None when zcore does not answer (UNKNOWN). A zcore
        that is not ACTIVE or a zboxapi below 0.2.1 is refused (409, 501)."""
        try:
            return zcore_storage(zpod, "the disk list").get("/disk")
        except HTTPException as e:
            if e.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
                return None
            raise

    @staticmethod
    def view(row: M.ZpodDisk | None, live: dict | None, known: bool) -> ZpodDiskView:
        if row is not None:
            kind = ZpodDiskKind(row.kind)
            if row.status == ZpodDiskStatus.PENDING:
                state = ZpodDiskStatus.PENDING
            elif not known:
                state = ZpodDiskStatus.UNKNOWN
            elif live is None:
                state = ZpodDiskStatus.MISSING
            else:
                state = ZpodDiskStatus.ACTIVE
        else:
            # A disk zcore has and no row describes: the deploy's own until the
            # first disk flow records them, or one added by hand.
            kind = (
                ZpodDiskKind.ZPOD
                if live["state"] in ("system", "protected")
                else ZpodDiskKind.USER
            )
            state = ZpodDiskStatus.ACTIVE
        return ZpodDiskView(
            id=row.id if row else None,
            device=f"/dev/{live['name']}" if live else None,
            scsi=f"0:{row.scsi_unit}" if row and row.scsi_unit is not None else None,
            size_gb=live["size_bytes"] // GIB if live else row.size_gb,
            state=live["state"] if live else None,
            storage=live.get("storage") if live else None,
            kind=kind,
            status=state,
            disk_uuid=row.disk_uuid if row else M.normalise_disk_uuid(live["serial"]),
        )

    def get_all(self, zpod: M.Zpod) -> list[ZpodDiskView]:
        live = self.live(zpod)
        by_uuid = {
            M.normalise_disk_uuid(d.get("serial")): d
            for d in (live or [])
            if d.get("serial")
        }
        views, matched = [], set()
        for row in zpod.disks:
            disk = by_uuid.get(row.disk_uuid) if row.disk_uuid else None
            if disk is not None:
                matched.add(disk["name"])
            views.append(self.view(row, disk, live is not None))
        for disk in live or []:
            if disk["name"] not in matched:
                views.append(self.view(None, disk, True))

        def order(v: ZpodDiskView):
            unit = int(v.scsi.split(":")[1]) if v.scsi else 99
            return (unit, v.device or "~", v.id or 0)

        return sorted(views, key=order)

    def find(self, zpod: M.Zpod, device: str) -> tuple[dict, M.ZpodDisk | None]:
        """The live disk named `device` and its row (None when it has none)."""
        name = device_name(device)
        live = zcore_storage(zpod, WHAT).get("/disk")
        for disk in live:
            if disk["name"] == name:
                uuid = M.normalise_disk_uuid(disk.get("serial"))
                row = next(
                    (r for r in zpod.disks if uuid and r.disk_uuid == uuid), None
                )
                return disk, row
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"zcore of zPod {zpod.name} has no disk /dev/{name}.",
        )

    def get_view(self, zpod: M.Zpod, device: str) -> ZpodDiskView:
        disk, row = self.find(zpod, device)
        return self.view(row, disk, True)

    def row_view(self, zpod: M.Zpod, row: M.ZpodDisk | None) -> ZpodDiskView | None:
        """The row as the list shows it, zcore asked once; None for a deleted row."""
        if row is None:
            return None
        for view in self.get_all(zpod):
            if view.id == row.id:
                return view
        return None

    # ── checks ───────────────────────────────────────────────────────────────

    def refuse_when_pending(self, zpod: M.Zpod):
        if any(d.status == ZpodDiskStatus.PENDING for d in zpod.disks):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"a disk change is already running on {zpod.name}; "
                "one at a time per zPod.",
            )

    def refuse_above_cap(self, size_gb: int):
        if self.is_superadmin:
            return
        try:
            cap = int(DBUtils.get_setting_value("zpodfactory_zpod_disk_max_gb"))
        except (TypeError, ValueError):
            cap = DEFAULT_DISK_MAX_GB
        if size_gb > cap:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"{size_gb} GiB is above the limit of {cap} GiB per disk "
                "(zpodfactory_zpod_disk_max_gb).",
            )

    @staticmethod
    def refuse_deploy_disk(disk: dict, row: M.ZpodDisk | None, action: str):
        """The deploy's disks: the system disk never changes, the filer disk only
        grows. A disk no row describes was not added through zPodFactory."""
        name = f"/dev/{disk['name']}"
        if disk["state"] == "system":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{name} is the zcore system disk: never changed here.",
            )
        if action == "grow":
            return
        if disk["state"] == "protected" or (row and row.kind == ZpodDiskKind.ZPOD):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{name} is the zcore filer disk, created and removed with the "
                "zPod only (grow is allowed).",
            )
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{name} was not added through zPodFactory: no disk row "
                "describes it.",
            )

    # ── changes ──────────────────────────────────────────────────────────────

    def schedule(self, flow: str, run_name: str, **params) -> str | None:
        run = ZpodEngineClient().create_flow_run_by_name(
            flow_name=flow, deployment_name=flow, run_name=run_name, **params
        )
        return (run or {}).get("id")

    def add(
        self, zpod: M.Zpod, size_gb: int, current_user: M.User
    ) -> tuple[M.ZpodDisk, str | None]:
        self.refuse_above_cap(size_gb)
        self.refuse_when_pending(zpod)
        zcore_storage(zpod, WHAT)  # zcore ACTIVE, zboxapi >= 0.2.1, answering
        disk = M.ZpodDisk(
            zpod_id=zpod.id,
            kind=ZpodDiskKind.USER.value,
            status=ZpodDiskStatus.PENDING.value,
            size_gb=size_gb,
        )
        self.session.add(disk)
        self.session.flush()
        run_id = self.schedule(
            "zpod_disk_add",
            f"add disk {zpod.name}/{size_gb}GiB by {current_user.username}",
            zpod_id=zpod.id,
            disk_id=disk.id,
            zpod_name=zpod.name,
            size_gb=size_gb,
            requested_by=current_user.username,
        )
        self.session.commit()
        return disk, run_id

    def grow(
        self, zpod: M.Zpod, device: str, size_gb: int, current_user: M.User
    ) -> tuple[M.ZpodDisk, str | None]:
        disk, row = self.find(zpod, device)
        self.refuse_deploy_disk(disk, row, "grow")
        if row is None:
            if not disk.get("serial"):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="zcore has no disk serials: power-cycle it once "
                    "(disk.EnableUUID is already set on its VM).",
                )
            if disk["state"] != "protected":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"/dev/{disk['name']} was not added through zPodFactory: "
                    "no disk row describes it.",
                )
            # The filer disk of a zPod deployed before zpod_disks: recorded now,
            # the flow adds its device key from vCenter.
            row = M.ZpodDisk(
                zpod_id=zpod.id,
                kind=ZpodDiskKind.ZPOD.value,
                status=ZpodDiskStatus.ACTIVE.value,
                size_gb=disk["size_bytes"] // GIB,
                disk_uuid=M.normalise_disk_uuid(disk["serial"]),
            )
        current = disk["size_bytes"] // GIB
        if size_gb <= current:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"/dev/{disk['name']} has {current} GiB; give a larger size "
                "(a disk only grows).",
            )
        self.refuse_above_cap(size_gb)
        self.refuse_when_pending(zpod)
        row.status = ZpodDiskStatus.PENDING.value
        self.session.add(row)
        self.session.flush()
        run_id = self.schedule(
            "zpod_disk_grow",
            f"grow disk {zpod.name}/{disk['name']} to {size_gb}GiB "
            f"by {current_user.username}",
            zpod_id=zpod.id,
            disk_id=row.id,
            size_gb=size_gb,
            zpod_name=zpod.name,
            device=disk["name"],
            requested_by=current_user.username,
        )
        self.session.commit()
        return row, run_id

    def remove(
        self, zpod: M.Zpod, device: str, current_user: M.User
    ) -> tuple[M.ZpodDisk, str | None]:
        disk, row = self.find(zpod, device)
        self.refuse_deploy_disk(disk, row, "remove")
        if disk["state"] not in REMOVABLE:
            used = f" by {disk['storage']}" if disk.get("storage") else ""
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"/dev/{disk['name']} is {disk['state']}{used}. "
                "Delete the storage first.",
            )
        self.refuse_when_pending(zpod)
        row.status = ZpodDiskStatus.PENDING.value
        self.session.add(row)
        self.session.flush()
        run_id = self.schedule(
            "zpod_disk_remove",
            f"remove disk {zpod.name}/{disk['name']} by {current_user.username}",
            zpod_id=zpod.id,
            disk_id=row.id,
            zpod_name=zpod.name,
            device=disk["name"],
            requested_by=current_user.username,
        )
        self.session.commit()
        return row, run_id

    # Prefect prefixes a failed run's message with the exception type.
    RUN_MESSAGE_PREFIX = re.compile(
        r"^Flow run encountered an exception: (?:[A-Za-z_.]*(?:Error|Exception): )?"
    )

    def run(self, zpod: M.Zpod, flow_run_id: str) -> dict:
        """A disk run of this zPod: its state and message, and the disk now."""
        run = ZpodEngineClient().get_flow_run(flow_run_id)
        params = (run or {}).get("parameters", {})
        if run is None or params.get("zpod_id") != zpod.id or "disk_id" not in params:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No disk run {flow_run_id} on zPod {zpod.name}.",
            )
        message = run.get("message")
        if message:
            message = self.RUN_MESSAGE_PREFIX.sub("", message, count=1)
        self.session.expire_all()
        row = self.session.get(M.ZpodDisk, params["disk_id"])
        return {
            "disk": self.row_view(zpod, row),
            "flow_run_id": flow_run_id,
            "name": run.get("name"),
            "state": run.get("state") or "UNKNOWN",
            "message": message,
        }
