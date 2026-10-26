from fastapi import APIRouter, status

from zpodapi.lib.global_dependencies import GlobalAnnotations
from zpodapi.lib.route_logger import RouteLogger

from .zpod__dependencies import ZpodAnnotations, ZpodDepends
from .zpod_disk__dependencies import ZpodDiskAnnotations
from .zpod_disk__schemas import (
    ZpodDiskCreate,
    ZpodDiskGrow,
    ZpodDiskRunView,
    ZpodDiskView,
)

router = APIRouter(
    prefix="/zpods/{id}/disks",
    tags=["zpods"],
    route_class=RouteLogger,
)


@router.get(
    "",
    summary="zPod Disk Get All",
    response_model=list[ZpodDiskView],
    dependencies=[ZpodDepends.ZpodReader],
)
def disks_get_all(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_disk_service: ZpodDiskAnnotations.ZpodDiskService,
):
    """The virtual disks of the zcore VM: the rows, matched live with what zcore sees."""
    return zpod_disk_service.get_all(zpod)


@router.get(
    "/runs/{flow_run_id}",
    summary="zPod Disk Run",
    response_model=ZpodDiskRunView,
    dependencies=[ZpodDepends.ZpodReader],
)
def disk_run(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_disk_service: ZpodDiskAnnotations.ZpodDiskService,
    flow_run_id: str,
):
    """The state of a disk add, grow or remove: the run's state and message (the
    failure when it failed) and the disk as it is now."""
    return zpod_disk_service.run(zpod, flow_run_id)


@router.get(
    "/{device}",
    summary="zPod Disk Get",
    response_model=ZpodDiskView,
    dependencies=[ZpodDepends.ZpodReader],
)
def disk_get(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_disk_service: ZpodDiskAnnotations.ZpodDiskService,
    device: str,
):
    return zpod_disk_service.get_view(zpod, device)


@router.post(
    "",
    summary="zPod Disk Add",
    response_model=ZpodDiskRunView,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def disk_add(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_disk_service: ZpodDiskAnnotations.ZpodDiskService,
    current_user: GlobalAnnotations.GetCurrentUser,
    disk_in: ZpodDiskCreate,
):
    """Add a thin disk of size_gb GiB to the zcore VM; follow the run for the device."""
    disk, run_id = zpod_disk_service.add(zpod, disk_in.size_gb, current_user)
    return ZpodDiskRunView(
        disk=zpod_disk_service.view(disk, None, True), flow_run_id=run_id
    )


@router.put(
    "/{device}/grow",
    summary="zPod Disk Grow",
    response_model=ZpodDiskRunView,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def disk_grow(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_disk_service: ZpodDiskAnnotations.ZpodDiskService,
    current_user: GlobalAnnotations.GetCurrentUser,
    device: str,
    grow_in: ZpodDiskGrow,
):
    """Grow a disk to size_gb GiB; what is on it grows with storage grow."""
    disk, run_id = zpod_disk_service.grow(zpod, device, grow_in.size_gb, current_user)
    return ZpodDiskRunView(
        disk=zpod_disk_service.view(disk, None, True), flow_run_id=run_id
    )


@router.delete(
    "/{device}",
    summary="zPod Disk Remove",
    response_model=ZpodDiskRunView,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def disk_remove(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_disk_service: ZpodDiskAnnotations.ZpodDiskService,
    current_user: GlobalAnnotations.GetCurrentUser,
    device: str,
):
    """Remove a blank or foreign user disk with its data (refused while in use)."""
    disk, run_id = zpod_disk_service.remove(zpod, device, current_user)
    return ZpodDiskRunView(
        disk=zpod_disk_service.view(disk, None, True), flow_run_id=run_id
    )
