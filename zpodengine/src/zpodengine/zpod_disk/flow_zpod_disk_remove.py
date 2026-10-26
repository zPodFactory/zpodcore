"""Remove a user disk from a zPod's zcore VM: detached in zcore, then deleted with
its file. Its data is gone (D14): the API refused while anything used it."""

from prefect import flow, task

from zpodcommon import models as M
from zpodcommon.enums import ZpodDiskStatus
from zpodengine.lib import database
from zpodengine.lib.options import task_options_setup
from zpodengine.zpod_disk.common import by_serial, load, zb_json, zbox, zcore_vm

REMOVABLE = ("blank", "foreign")


@task
def zpod_disk_remove_zcore(zpod_id: int, disk_id: int) -> None:
    """The kernel forgets the device; zboxapi refuses when anything is mounted."""
    with database.get_session_ctx() as session:
        zpod, disk = load(session, zpod_id, disk_id)
        zb = zbox(zpod)
        live = by_serial(zb_json(zb.get(url="/disk")), disk.disk_uuid)
        if live is None:
            print("zcore: the disk is not attached in zcore (already detached)")
            return
        if live["state"] not in REMOVABLE:
            raise RuntimeError(
                f"/dev/{live['name']} is {live['state']}"
                + (f" by {live['storage']}" if live.get("storage") else "")
                + ": not removed"
            )
        zb_json(zb.post(url=f"/disk/{live['name']}/detach"))
        print(f"zcore: /dev/{live['name']} detached")


@task
def zpod_disk_remove_vcenter(zpod_id: int, disk_id: int) -> None:
    with database.get_session_ctx() as session:
        zpod, disk = load(session, zpod_id, disk_id)
        with zcore_vm(zpod) as (vc, vm):
            try:
                vc.remove_vdisk(vm, disk.disk_uuid, disk.vm_disk_key)
                print(
                    f"vCenter: disk {disk.vm_disk_key} (SCSI 0:{disk.scsi_unit}) "
                    "removed, file deleted"
                )
            except LookupError:
                print("vCenter: the disk is not on the zcore VM any more")
        session.delete(disk)
        session.commit()
        print("disk removed")


def flow_failed(flow, flow_run, state):
    from prefect.logging.loggers import flow_run_logger

    logger = flow_run_logger(flow_run, flow)
    with database.get_session_ctx() as session:
        disk = session.get(M.ZpodDisk, flow_run.parameters["disk_id"])
        if disk is not None:
            disk.status = ZpodDiskStatus.ACTIVE.value
            session.add(disk)
            session.commit()
            logger.info("disk row back to ACTIVE; a new remove repeats both steps")


@flow(
    name="zpod_disk_remove",
    flow_run_name="remove disk {zpod_name}/{device} by {requested_by}",
    on_failure=[flow_failed],
    log_prints=True,
)
def flow_zpod_disk_remove(
    zpod_id: int,
    disk_id: int,
    zpod_name: str,
    device: str,
    requested_by: str,
) -> None:
    options = task_options_setup(prefix=f"{zpod_name} disk remove {device}")
    detached = zpod_disk_remove_zcore.with_options(**options(name="zcore")).submit(
        zpod_id=zpod_id, disk_id=disk_id
    )
    detached.result()
    removed = zpod_disk_remove_vcenter.with_options(**options(name="vcenter")).submit(
        zpod_id=zpod_id, disk_id=disk_id, wait_for=[detached]
    )
    removed.result()
