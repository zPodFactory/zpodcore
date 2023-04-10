from fastapi import APIRouter

from .instance__dependencies import InstanceAnnotations
from .instance_feature__schemas import InstanceFeatureView

router = APIRouter(
    prefix="/instances/{id}/features",
    tags=["instances"],
)


@router.get(
    "",
    response_model=list[InstanceFeatureView],
)
def instance_features_get_all(
    *,
    instance: InstanceAnnotations.GetInstance,
):
    return instance.features
