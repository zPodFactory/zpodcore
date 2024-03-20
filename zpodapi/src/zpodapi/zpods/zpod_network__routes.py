from fastapi import APIRouter

from .zpod__dependencies import ZpodAnnotations
from .zpod_network__schemas import ZpodNetworkView

router = APIRouter(
    prefix="/zpods/{id}/networks",
    tags=["zpods"],
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
