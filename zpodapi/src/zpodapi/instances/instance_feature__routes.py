from fastapi import APIRouter, Depends

from zpodapi.lib import dependencies
from zpodcommon import models as M

from . import instance__dependencies
from .instance_feature__schemas import InstanceFeatureView

router = APIRouter(
    prefix="/instances/{id}/features",
    tags=["instances"],
    dependencies=[Depends(dependencies.get_current_user_and_update)],
)


@router.get(
    "",
    response_model=list[InstanceFeatureView],
)
def features_get_all(
    *,
    instance: M.Instance = Depends(instance__dependencies.get_instance_record),
):
    return instance.features
