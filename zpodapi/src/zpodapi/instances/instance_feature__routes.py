from fastapi import APIRouter

from zpodapi.lib import dependencies

from . import instance__dependencies
from .instance_feature__schemas import InstanceFeatureView

router = APIRouter(
    prefix="/instances/{id}/features",
    tags=["instances"],
    dependencies=[dependencies.GetCurrentUserAndUpdateDepends],
)


@router.get(
    "",
    response_model=list[InstanceFeatureView],
)
def features_get_all(
    *,
    instance: instance__dependencies.GetInstanceRecord,
):
    return instance.features
