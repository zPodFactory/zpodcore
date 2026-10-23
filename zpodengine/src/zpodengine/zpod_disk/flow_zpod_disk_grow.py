"""Grow a virtual disk of a zPod's zcore VM; what is on it grows with storage grow."""

from prefect import flow, task

from zpodcommon import models as M
from zpodcommon.enums import ZpodDiskStatus
from zpodengine.lib import database
from zpodengine.lib.datastore_floor import check_datastore_floor
from zpodengine.lib.options import task_options_setup
from zpodengine.zpod_disk.common import (
    GIB,
    ensure_deploy_rows,
    load,
    zb_json,
    zbox,
    zcore_vm,
)


@task
def zpod_disk_grow_vcenter(zpod_id: int, disk_id: int, size_gb: int) -> None:
    with database.get_session_ctx() as session:
        zpod, disk = load(session, zpod_id, disk_id)
        zbox(zpod)
        with zcore_vm(zpod) as (vc, vm):
            ensure_deploy_rows(session, zpod, vc, vm)
            session.refresh(disk)
            vdisk = vc.vdisk(vm, disk.disk_uuid, disk.vm_disk_key)
            current = vdisk.capacityInBytes // GIB
            if size_gb <= current:
                raise ValueError(
                    f"the disk has {current} GiB already; a disk only grows"
                )
            check_datastore_floor(
                vc.vm_datastore(vm), size_gb - current, f"disk grow {zpod.name}"
            )
            vdisk = vc.grow_vdisk(vm, disk.disk_uuid, vdisk.key, size_gb)
            disk.size_gb = vdisk.capacityInBytes // GIB
            session.add(disk)
            session.commit()
            print(
                f"vCenter: disk {vdisk.key} (SCSI 0:{vdisk.unitNumber}) grown "
                f"from {current} GiB to {disk.size_gb} GiB"
            )


@task
def zpod_disk_grow_zcore(zpod_id: int, disk_id: int) -> str:
    with database.get_session_ctx() as session:
        zpod, disk = load(session, zpod_id, disk_id)
        rescan = zb_json(zbox(zpod).post(url="/disk/rescan"))
        for r in rescan["resized"]:
            print(
                f"zcore: rescan: /dev/{r['disk']} {r['before_bytes'] // GIB} GiB → "
                f"{r['after_bytes'] // GIB} GiB"
                + (
                    f" ({r['storage']}: storage grow uses the space)"
                    if r["storage"]
                    else ""
                )
            )
        disk.status = ZpodDiskStatus.ACTIVE.value
        session.add(disk)
        session.commit()
        for d in rescan["disks"]:
            if M.normalise_disk_uuid(d.get("serial")) == disk.disk_uuid:
                return d["name"]
        return ""


def flow_failed(flow, flow_run, state):
    from prefect.logging.loggers import flow_run_logger

    logger = flow_run_logger(flow_run, flow)
    with database.get_session_ctx() as session:
        disk = session.get(M.ZpodDisk, flow_run.parameters["disk_id"])
        if disk is not None:
            disk.status = ZpodDiskStatus.ACTIVE.value
            session.add(disk)
            session.commit()
            logger.info(f"disk row back to ACTIVE ({disk.size_gb} GiB)")


@flow(
    name="zpod_disk_grow",
    flow_run_name="grow disk {zpod_name}/{device} to {size_gb}GiB by {requested_by}",
    on_failure=[flow_failed],
    log_prints=True,
)
def flow_zpod_disk_grow(
    zpod_id: int,
    disk_id: int,
    size_gb: int,
    zpod_name: str,
    device: str,
    requested_by: str,
) -> str:
    options = task_options_setup(prefix=f"{zpod_name} disk grow {device}")
    grown = zpod_disk_grow_vcenter.with_options(**options(name="vcenter")).submit(
        zpod_id=zpod_id, disk_id=disk_id, size_gb=size_gb
    )
    grown.result()
    rescanned = zpod_disk_grow_zcore.with_options(**options(name="zcore")).submit(
        zpod_id=zpod_id, disk_id=disk_id, wait_for=[grown]
    )
    return rescanned.result()
