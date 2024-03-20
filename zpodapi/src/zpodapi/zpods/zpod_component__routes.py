from fastapi import APIRouter, status

from .zpod__dependencies import ZpodAnnotations, ZpodDepends
from .zpod_component__dependencies import ZpodComponentAnnotations
from .zpod_component__schemas import ZpodComponentCreate, ZpodComponentView

router = APIRouter(
    prefix="/zpods/{id}/components",
    tags=["zpods"],
)


@router.get(
    "",
    summary="zPod Component Get All",
    response_model=list[ZpodComponentView],
    response_model_exclude_unset=True,
)
def components_get_all(
    *,
    zpod: ZpodAnnotations.GetZpod,
):
    return zpod.components


@router.get(
    "/{component_id}",
    summary="zPod Component Get",
    response_model=ZpodComponentView,
    response_model_exclude_unset=True,
)
def components_get(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_component: ZpodComponentAnnotations.GetZpodComponent,
):
    return zpod_component


@router.post(
    "",
    summary="zPod Component Add",
    status_code=status.HTTP_201_CREATED,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def components_add(
    *,
    zpod_component_service: ZpodComponentAnnotations.ZpodComponentService,
    zpod: ZpodAnnotations.GetZpod,
    component_in: ZpodComponentCreate,
):
    return zpod_component_service.add(
        zpod=zpod,
        component_in=component_in,
    )


@router.delete(
    "/{component_id}",
    summary="zPod Component Remove",
    status_code=status.HTTP_204_NO_CONTENT,
)
def components_remove(
    *,
    zpod_component_service: ZpodComponentAnnotations.ZpodComponentService,
    zpod_component: ZpodComponentAnnotations.GetZpodComponent,
):
    return zpod_component_service.remove(zpod_component=zpod_component)
