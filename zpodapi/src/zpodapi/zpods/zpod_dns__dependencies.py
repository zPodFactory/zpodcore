from ipaddress import IPv4Address
from typing import Annotated

from fastapi import Depends

from zpodapi.lib.global_dependencies import service_init_annotation
from zpodapi.lib.types import HOSTNAME

from .zpod__dependencies import ZpodAnnotations
from .zpod_dns__services import ZpodDnsService


def get_zpod_dns(
    *,
    zpod_dns_service: "ZpodDnsAnnotations.ZpodDnsService",
    zpod: ZpodAnnotations.GetZpod,
    ip: IPv4Address,
    hostname: HOSTNAME,
):
    return zpod_dns_service.get(zpod, ip, hostname)


class ZpodDnsDepends:
    pass


class ZpodDnsAnnotations:
    ZpodDnsService = service_init_annotation(ZpodDnsService)
    GetZpodDns = Annotated[
        dict,
        Depends(get_zpod_dns),
    ]
