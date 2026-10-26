"""What the three disk flows share: the rows, the zcore VM, zboxapi."""

from contextlib import contextmanager

from pyVmomi import vim
from sqlmodel import Session

from zpodcommon import models as M
from zpodcommon.enums import ZpodDiskKind, ZpodDiskStatus
from zpodcommon.lib.vmware import vCenter
from zpodcommon.lib.zboxapi import ZboxApiClient, ZboxApiTooOld, require_zboxapi

GIB = 1024**3
# The deploy's two disks: the system disk and the filer disk (STORAGE01).
DEPLOY_UNITS = (0, 1)
NO_SERIALS = (
    "zcore has no disk serials: power-cycle it once "
    "(disk.EnableUUID is already set on its VM)"
)


def load(session: Session, zpod_id: int, disk_id: int) -> tuple[M.Zpod, M.ZpodDisk]:
    zpod = session.get(M.Zpod, zpod_id)
    if zpod is None:
        raise ValueError(f"zPod {zpod_id} not found")
    disk = session.get(M.ZpodDisk, disk_id)
    if disk is None or disk.zpod_id != zpod.id:
        raise ValueError(f"disk {disk_id} not found on zPod {zpod.name}")
    return zpod, disk


def zcore_fqdn(zpod: M.Zpod) -> str:
    for c in zpod.components:
        if c.component.component_name == "zcore":
            return c.fqdn
    raise ValueError(f"zPod {zpod.name} has no zcore component")


@contextmanager
def zcore_vm(zpod: M.Zpod):
    """vCenter of the zPod's endpoint and the zcore VM on it."""
    with vCenter.auth_by_zpod_endpoint(zpod=zpod) as vc:
        vm = vc.get_vm(name=zcore_fqdn(zpod))
        if vm is None:
            raise LookupError(f"zcore VM {zcore_fqdn(zpod)} not found in vCenter")
        yield vc, vm


def zbox(zpod: M.Zpod) -> ZboxApiClient:
    """zboxapi of the zPod, checked for the storage capabilities (D19)."""
    zb = ZboxApiClient.by_zpod(zpod)
    try:
        require_zboxapi(zb, zpod.name)
    except ZboxApiTooOld as e:
        raise ValueError(str(e)) from e
    return zb


def zb_json(response):
    """The answer of a zboxapi call, or an error that says what zboxapi said."""
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise RuntimeError(
            f"zboxapi {response.request.method} {response.request.url.path}: "
            f"{detail} [{response.status_code}]"
        )
    return response.json()


def by_serial(disks: list[dict], disk_uuid: str) -> dict | None:
    for d in disks:
        if M.normalise_disk_uuid(d.get("serial")) == disk_uuid:
            return d
    return None


def ensure_deploy_rows(
    session: Session, zpod: M.Zpod, vc: vCenter, vm: vim.VirtualMachine
) -> None:
    """The deploy's two disks as rows, for a zPod deployed before zpod_disks: read
    from vCenter (units 0 and 1 of the first SCSI controller). A row the API made
    for one of them (a grow of the filer disk) gets its key and unit."""
    rows = {d.disk_uuid: d for d in zpod.disks if d.disk_uuid}
    for vdisk in vc.vdisks(vm):
        if (
            vdisk.controllerKey != vc.SCSI_CONTROLLER_KEY
            or vdisk.unitNumber not in DEPLOY_UNITS
        ):
            continue
        uuid = M.normalise_disk_uuid(vdisk.backing.uuid)
        row = rows.get(uuid)
        if row is None:
            row = M.ZpodDisk(
                zpod_id=zpod.id,
                kind=ZpodDiskKind.ZPOD.value,
                status=ZpodDiskStatus.ACTIVE.value,
                size_gb=vdisk.capacityInBytes // GIB,
                disk_uuid=uuid,
            )
            print(f"Deploy disk on SCSI 0:{vdisk.unitNumber} recorded ({uuid})")
        row.scsi_unit = vdisk.unitNumber
        row.vm_disk_key = vdisk.key
        session.add(row)
    session.commit()
    session.refresh(zpod)
