from fastapi import APIRouter

from zpodapi.lib import dependencies
from zpodcommon import models as M

from . import instance__dependencies
from .instance_network__schemas import InstanceNetworkView

router = APIRouter(
    prefix="/instances/{id}/networks",
    tags=["instances"],
    dependencies=[dependencies.GetCurrentUserAndUpdateDepends],
)


@router.get(
    "",
    response_model=list[InstanceNetworkView],
)
def networks_get_all(
    *,
    instance: M.Instance = instance__dependencies.GetInstanceRecord,
):
    return instance.networks
