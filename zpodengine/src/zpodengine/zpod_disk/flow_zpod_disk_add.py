"""Add a thin disk to a zPod's zcore VM, found in zcore by its serial."""

from prefect import flow, task

from zpodcommon import models as M
from zpodcommon.enums import ZpodDiskStatus
from zpodengine.lib import database
from zpodengine.lib.datastore_floor import check_datastore_floor
from zpodengine.lib.options import task_options_setup
from zpodengine.zpod_disk.common import (
    NO_SERIALS,
    by_serial,
    ensure_deploy_rows,
    load,
    zb_json,
    zbox,
    zcore_vm,
)


@task
def zpod_disk_add_vcenter(zpod_id: int, disk_id: int) -> None:
    """Datastore floor, then the disk on the next free SCSI unit; the row gets its
    unit, device key and disk UUID."""
    with database.get_session_ctx() as session:
        zpod, disk = load(session, zpod_id, disk_id)
        zbox(zpod)  # zboxapi >= 0.2.1 before vSphere is touched
        with zcore_vm(zpod) as (vc, vm):
            if vc.set_disk_enable_uuid(vm):
                print(
                    "disk.EnableUUID was not set on the zcore VM: set now, read by "
                    "zcore at its next power-on"
                )
            ensure_deploy_rows(session, zpod, vc, vm)
            check_datastore_floor(
                vc.vm_datastore(vm), disk.size_gb, f"disk add {zpod.name}"
            )
            unit = vc.next_free_scsi_unit(vm)
            vdisk = vc.add_vdisk(vm, disk.size_gb, unit)
            disk.scsi_unit = unit
            disk.vm_disk_key = vdisk.key
            disk.disk_uuid = M.normalise_disk_uuid(vdisk.backing.uuid)
            session.add(disk)
            session.commit()
            print(
                f"vCenter: {disk.size_gb} GiB thin disk added on SCSI 0:{unit} "
                f"(device key {vdisk.key})"
            )


@task
def zpod_disk_add_zcore(zpod_id: int, disk_id: int) -> str:
    """zboxapi rescans and lists every disk: ours is the one with its serial."""
    with database.get_session_ctx() as session:
        zpod, disk = load(session, zpod_id, disk_id)
        rescan = zb_json(zbox(zpod).post(url="/disk/rescan"))
        found = by_serial(rescan["disks"], disk.disk_uuid)
        if found is None:
            if any(not d.get("serial") for d in rescan["disks"]):
                raise RuntimeError(NO_SERIALS)
            raise RuntimeError(
                f"zcore does not see the disk with serial {disk.disk_uuid} after a rescan"
            )
        disk.status = ZpodDiskStatus.ACTIVE.value
        disk.size_gb = found["size_bytes"] // 1024**3
        session.add(disk)
        session.commit()
        print(f"zcore: /dev/{found['name']} has the disk's serial, {found['state']}")
        return found["name"]


def flow_failed(flow, flow_run, state):
    """Nothing half-done stays: the disk, when vCenter added it, goes (checked by
    key and UUID), and so does the row."""
    from prefect.logging.loggers import flow_run_logger

    from zpodengine.zpod_disk.common import zcore_vm as vm_of

    logger = flow_run_logger(flow_run, flow)
    with database.get_session_ctx() as session:
        disk = session.get(M.ZpodDisk, flow_run.parameters["disk_id"])
        if disk is None:
            return
        zpod = disk.zpod
        if disk.disk_uuid:
            try:
                with vm_of(zpod) as (vc, vm):
                    vc.remove_vdisk(vm, disk.disk_uuid, disk.vm_disk_key)
                logger.info(f"disk {disk.disk_uuid} removed from the zcore VM")
            except Exception as e:  # noqa: BLE001  report, still drop the row
                logger.error(f"disk {disk.disk_uuid} could not be removed: {e}")
        session.delete(disk)
        session.commit()
        logger.info("disk row deleted")


@flow(
    name="zpod_disk_add",
    flow_run_name="add disk {zpod_name}/{size_gb}GiB by {requested_by}",
    on_failure=[flow_failed],
    log_prints=True,
)
def flow_zpod_disk_add(
    zpod_id: int,
    disk_id: int,
    zpod_name: str,
    size_gb: int,
    requested_by: str,
) -> str:
    """The API wrote the row (PENDING, size_gb); ``zpod_name``, ``size_gb`` and
    ``requested_by`` are for the run name."""
    options = task_options_setup(prefix=f"{zpod_name} disk add")
    added = zpod_disk_add_vcenter.with_options(**options(name="vcenter")).submit(
        zpod_id=zpod_id, disk_id=disk_id
    )
    added.result()
    found = zpod_disk_add_zcore.with_options(**options(name="zcore")).submit(
        zpod_id=zpod_id, disk_id=disk_id, wait_for=[added]
    )
    return found.result()
