from fastapi import APIRouter

from .zpod__dependencies import ZpodAnnotations
from .zpod_feature__schemas import ZpodFeatureView

router = APIRouter(
    prefix="/zpods/{id}/features",
    tags=["zpods"],
)


@router.get(
    "",
    summary="zPod Feature Get All",
    response_model=list[ZpodFeatureView],
)
def features_get_all(
    *,
    zpod: ZpodAnnotations.GetZpod,
):
    return zpod.features
