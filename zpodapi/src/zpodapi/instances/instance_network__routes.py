from fastapi import APIRouter

from .instance__dependencies import InstanceAnnotations
from .instance_network__schemas import InstanceNetworkView

router = APIRouter(
    prefix="/instances/{id}/networks",
    tags=["instances"],
)


@router.get(
    "",
    response_model=list[InstanceNetworkView],
)
def instance_networks_get_all(
    *,
    instance: InstanceAnnotations.GetInstance,
):
    return instance.networks
