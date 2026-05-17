from fastapi import APIRouter

from zpodapi.lib.route_logger import RouteLogger

from .zpod__dependencies import ZpodAnnotations
from .zpod_network__schemas import ZpodNetworkView

router = APIRouter(
    prefix="/zpods/{id}/networks",
    tags=["zpods"],
    route_class=RouteLogger,
)


@router.get(
    "",
    summary="zPod Network Get All",
    response_model=list[ZpodNetworkView],
)
def networks_get_all(
    *,
    zpod: ZpodAnnotations.GetZpod,
):
    return zpod.networks
