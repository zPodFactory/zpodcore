from fastapi import APIRouter

from zpodapi.lib.global_dependencies import GlobalDepends

from .instance__dependencies import InstanceAnnotations
from .instance_network__schemas import InstanceNetworkView

router = APIRouter(
    prefix="/instances/{id}/networks",
    tags=["instances"],
    dependencies=[GlobalDepends.UpdateLastConnectionDate],
)


@router.get(
    "",
    response_model=list[InstanceNetworkView],
)
def networks_get_all(
    *,
    instance: InstanceAnnotations.GetInstance,
):
    return instance.networks
