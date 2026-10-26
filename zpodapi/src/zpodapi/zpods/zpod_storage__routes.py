from fastapi import APIRouter, status

from zpodapi.lib.route_logger import RouteLogger

from .zpod__dependencies import ZpodAnnotations, ZpodDepends
from .zpod_storage__dependencies import ZpodStorageAnnotations
from .zpod_storage__schemas import (
    ZpodStorageAdopt,
    ZpodStorageCreate,
    ZpodStorageFolderCreate,
    ZpodStorageFolderRemoved,
    ZpodStorageFolderUpdate,
    ZpodStorageFolderView,
    ZpodStorageOperation,
    ZpodStorageView,
)

router = APIRouter(
    prefix="/zpods/{id}/storages",
    tags=["zpods"],
    route_class=RouteLogger,
)


@router.get(
    "",
    summary="zPod Storage Get All",
    response_model=list[ZpodStorageView],
    dependencies=[ZpodDepends.ZpodReader],
)
def storages_get_all(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_storage_service: ZpodStorageAnnotations.ZpodStorageService,
):
    """The filesystems zcore mounts under /FILER, with their folders, live."""
    return zpod_storage_service.get_all(zpod)


@router.get(
    "/{name}",
    summary="zPod Storage Get",
    response_model=ZpodStorageView,
    dependencies=[ZpodDepends.ZpodReader],
)
def storage_get(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_storage_service: ZpodStorageAnnotations.ZpodStorageService,
    name: str,
):
    return zpod_storage_service.get(zpod, name)


@router.post(
    "",
    summary="zPod Storage Create",
    response_model=ZpodStorageOperation,
    status_code=status.HTTP_201_CREATED,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def storage_create(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_storage_service: ZpodStorageAnnotations.ZpodStorageService,
    storage_in: ZpodStorageCreate,
    dry_run: bool = False,
    verbose: bool = False,
):
    """Partition, format and mount a blank disk of the zPod as /FILER/STORAGEnn."""
    return zpod_storage_service.create(zpod, storage_in, dry_run, verbose)


@router.post(
    "/adopt",
    summary="zPod Storage Adopt",
    response_model=ZpodStorageOperation,
    status_code=status.HTTP_201_CREATED,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def storage_adopt(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_storage_service: ZpodStorageAnnotations.ZpodStorageService,
    adopt_in: ZpodStorageAdopt,
    dry_run: bool = False,
    verbose: bool = False,
):
    """Mount an existing ext4 filesystem again (a deleted storage), data intact."""
    return zpod_storage_service.adopt(zpod, adopt_in, dry_run, verbose)


@router.put(
    "/{name}/grow",
    summary="zPod Storage Grow",
    response_model=ZpodStorageOperation,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def storage_grow(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_storage_service: ZpodStorageAnnotations.ZpodStorageService,
    name: str,
    dry_run: bool = False,
    verbose: bool = False,
):
    """Grow the partition (or LV) and filesystem into the space a disk grow made."""
    return zpod_storage_service.grow(zpod, name, dry_run, verbose)


@router.delete(
    "/{name}",
    summary="zPod Storage Delete",
    response_model=ZpodStorageOperation,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def storage_delete(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_storage_service: ZpodStorageAnnotations.ZpodStorageService,
    name: str,
    dry_run: bool = False,
    verbose: bool = False,
):
    """Unmount and forget the mount unit; the filesystem stays on the disk (409
    while it has exports)."""
    return zpod_storage_service.delete(zpod, name, dry_run, verbose)


@router.post(
    "/{name}/folders/{folder}",
    summary="zPod Storage Folder Add",
    response_model=ZpodStorageFolderView,
    status_code=status.HTTP_201_CREATED,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def storage_folder_add(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_storage_service: ZpodStorageAnnotations.ZpodStorageService,
    name: str,
    folder: str,
    folder_in: ZpodStorageFolderCreate,
):
    return zpod_storage_service.folder_add(zpod, name, folder, folder_in)


@router.put(
    "/{name}/folders/{folder}",
    summary="zPod Storage Folder Set",
    response_model=ZpodStorageFolderView,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def storage_folder_set(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_storage_service: ZpodStorageAnnotations.ZpodStorageService,
    name: str,
    folder: str,
    folder_in: ZpodStorageFolderUpdate,
):
    """chown and/or chmod a folder, optionally everything below it."""
    return zpod_storage_service.folder_set(zpod, name, folder, folder_in)


@router.delete(
    "/{name}/folders/{folder}",
    summary="zPod Storage Folder Remove",
    response_model=ZpodStorageFolderRemoved,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def storage_folder_remove(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_storage_service: ZpodStorageAnnotations.ZpodStorageService,
    name: str,
    folder: str,
    force: bool = False,
):
    """Delete an unexported folder: empty, or with everything in it when force."""
    return zpod_storage_service.folder_remove(zpod, name, folder, force)
