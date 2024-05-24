from fastapi import APIRouter, HTTPException, status

from .zpod__dependencies import ZpodAnnotations, ZpodDepends
from .zpod_dns__dependencies import ZpodDnsAnnotations
from .zpod_dns__schemas import ZpodDnsCreate, ZpodDnsUpdate, ZpodDnsView

router = APIRouter(
    prefix="/zpods/{id}/dns",
    tags=["zpods"],
)


@router.get(
    "",
    summary="zPod Dns Get All",
    response_model=list[ZpodDnsView],
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def dns_get_all(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_dns_service: ZpodDnsAnnotations.ZpodDnsService,
):
    return zpod_dns_service.get_all(zpod)


@router.get(
    "/{ip}/{hostname}",
    summary="zPod Dns Get",
    response_model=ZpodDnsView,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def dns_get(
    *,
    zpod_dns: ZpodDnsAnnotations.GetZpodDns,
):
    return zpod_dns


@router.post(
    "",
    summary="zPod Dns Add",
    status_code=status.HTTP_201_CREATED,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def dns_add(
    *,
    zpod_dns_service: ZpodDnsAnnotations.ZpodDnsService,
    zpod: ZpodAnnotations.GetZpod,
    dns_in: ZpodDnsCreate,
):
    if dns_in.host_id and dns_in.ip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must have ip or host_id, not both",
        )
    elif not dns_in.host_id and not dns_in.ip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must have ip or host_id",
        )

    return zpod_dns_service.add(
        zpod=zpod,
        hostname=dns_in.hostname,
        ip=dns_in.ip,
        host_id=dns_in.host_id,
    )


@router.put(
    "/{ip}/{hostname}",
    summary="zPod Dns Update",
    status_code=status.HTTP_201_CREATED,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def dns_update(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_dns_service: ZpodDnsAnnotations.ZpodDnsService,
    zpod_dns: ZpodDnsAnnotations.GetZpodDns,
    dns_in: ZpodDnsUpdate,
):
    return zpod_dns_service.update(
        zpod=zpod,
        hostname=zpod_dns["hostname"],
        ip=zpod_dns["ip"],
        newhostname=dns_in.hostname,
        newip=dns_in.ip,
        newhost_id=dns_in.host_id,
    )


@router.delete(
    "/{ip}/{hostname}",
    summary="zPod Dns Remove",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def dns_remove(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_dns_service: ZpodDnsAnnotations.ZpodDnsService,
    zpod_dns: ZpodDnsAnnotations.GetZpodDns,
):
    zpod_dns_service.remove(
        zpod=zpod,
        ip=str(zpod_dns["ip"]),
        hostname=zpod_dns["hostname"],
    )
