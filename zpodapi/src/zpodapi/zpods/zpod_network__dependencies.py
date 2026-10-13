from typing import Annotated

from fastapi import Depends

from zpodapi.lib.global_dependencies import service_init_annotation
from zpodcommon import models as M

from .zpod__dependencies import ZpodAnnotations
from .zpod_network__services import ZpodNetworkService


def get_zpod_network(
    *,
    zpod_network_service: "ZpodNetworkAnnotations.ZpodNetworkService",
    zpod: ZpodAnnotations.GetZpod,
    name: str,
):
    return zpod_network_service.get(zpod=zpod, name=name)


class ZpodNetworkDepends:
    pass


class ZpodNetworkAnnotations:
    ZpodNetworkService = service_init_annotation(ZpodNetworkService)
    GetZpodNetwork = Annotated[
        M.ZpodNetwork,
        Depends(get_zpod_network),
    ]
