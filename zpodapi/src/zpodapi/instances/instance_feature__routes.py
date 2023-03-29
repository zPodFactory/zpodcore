from fastapi import APIRouter

from zpodapi.lib.global_dependencies import GlobalDepends

from .instance__dependencies import InstanceAnnotations
from .instance_feature__schemas import InstanceFeatureView

router = APIRouter(
    prefix="/instances/{id}/features",
    tags=["instances"],
    dependencies=[GlobalDepends.UpdateLastConnectionDate],
)


@router.get(
    "",
    response_model=list[InstanceFeatureView],
)
def features_get_all(
    *,
    instance: InstanceAnnotations.GetInstance,
):
    return instance.features
