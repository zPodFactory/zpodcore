from fastapi import APIRouter, Response, status

from zpodapi.lib.route_logger import RouteLogger

from .zpod__dependencies import ZpodAnnotations, ZpodDepends
from .zpod_nfs__dependencies import ZpodNfsAnnotations
from .zpod_nfs__schemas import (
    ZpodNfsClientAdd,
    ZpodNfsCreate,
    ZpodNfsExportRemoved,
    ZpodNfsExportView,
    ZpodNfsStatus,
    ZpodNfsUpdate,
)

router = APIRouter(
    prefix="/zpods/{id}/nfs",
    tags=["zpods"],
    route_class=RouteLogger,
)


@router.get(
    "",
    summary="zPod NFS Export Get All",
    response_model=list[ZpodNfsExportView],
    dependencies=[ZpodDepends.ZpodReader],
)
def nfs_get_all(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_nfs_service: ZpodNfsAnnotations.ZpodNfsService,
):
    """Every export of zcore: /etc/exports (owner system) and the user-defined ones."""
    return zpod_nfs_service.get_all(zpod)


@router.get(
    "/status",
    summary="zPod NFS Status",
    response_model=ZpodNfsStatus,
    dependencies=[ZpodDepends.ZpodReader],
)
def nfs_status(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_nfs_service: ZpodNfsAnnotations.ZpodNfsService,
):
    """The NFS server of zcore: service, versions, threads, and the mounted clients."""
    return zpod_nfs_service.status(zpod)


@router.get(
    "/{storage}/{folder}",
    summary="zPod NFS Export Get",
    response_model=ZpodNfsExportView,
    dependencies=[ZpodDepends.ZpodReader],
)
def nfs_get(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_nfs_service: ZpodNfsAnnotations.ZpodNfsService,
    storage: str,
    folder: str,
):
    return zpod_nfs_service.get(zpod, storage, folder)


@router.post(
    "",
    summary="zPod NFS Export Add",
    response_model=ZpodNfsExportView,
    status_code=status.HTTP_201_CREATED,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def nfs_add(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_nfs_service: ZpodNfsAnnotations.ZpodNfsService,
    export_in: ZpodNfsCreate,
):
    """Export a folder of a storage (created when missing); clients default to *."""
    return zpod_nfs_service.add(zpod, export_in)


@router.put(
    "/{storage}/{folder}",
    summary="zPod NFS Export Set",
    response_model=ZpodNfsExportView,
    responses={201: {"model": ZpodNfsExportView}},
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def nfs_set(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_nfs_service: ZpodNfsAnnotations.ZpodNfsService,
    storage: str,
    folder: str,
    export_in: ZpodNfsUpdate,
    response: Response,
):
    """Make the export exactly this: 200 when replaced, 201 when created."""
    return zpod_nfs_service.set(zpod, storage, folder, export_in, response)


@router.post(
    "/{storage}/{folder}/clients",
    summary="zPod NFS Export Client Add",
    response_model=ZpodNfsExportView,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def nfs_client_add(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_nfs_service: ZpodNfsAnnotations.ZpodNfsService,
    storage: str,
    folder: str,
    client_in: ZpodNfsClientAdd,
):
    return zpod_nfs_service.client_add(zpod, storage, folder, client_in)


@router.delete(
    "/{storage}/{folder}/clients/{client:path}",
    summary="zPod NFS Export Client Remove",
    response_model=ZpodNfsExportView | ZpodNfsExportRemoved,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def nfs_client_remove(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_nfs_service: ZpodNfsAnnotations.ZpodNfsService,
    storage: str,
    folder: str,
    client: str,
):
    """Remove one client; the last one removes the export (the folder stays)."""
    return zpod_nfs_service.client_remove(zpod, storage, folder, client)


@router.delete(
    "/{storage}/{folder}",
    summary="zPod NFS Export Remove",
    response_model=ZpodNfsExportRemoved,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def nfs_remove(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_nfs_service: ZpodNfsAnnotations.ZpodNfsService,
    storage: str,
    folder: str,
):
    """Stop exporting a folder; the folder and its data stay."""
    return zpod_nfs_service.remove(zpod, storage, folder)
