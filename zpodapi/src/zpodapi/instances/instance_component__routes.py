from fastapi import APIRouter, status

from .instance__dependencies import InstanceAnnotations, InstanceDepends
from .instance_component__dependencies import InstanceComponentAnnotations
from .instance_component__schemas import InstanceComponentCreate, InstanceComponentView

router = APIRouter(
    prefix="/instances/{id}/components",
    tags=["instances"],
)


@router.get(
    "",
    summary="Instance Component Get All",
    response_model=list[InstanceComponentView],
    response_model_exclude_unset=True,
)
def components_get_all(
    *,
    instance: InstanceAnnotations.GetInstance,
):
    return instance.components


@router.get(
    "/{component_id}",
    summary="Instance Component Get",
    response_model=InstanceComponentView,
    response_model_exclude_unset=True,
)
def components_get(
    *,
    instance: InstanceAnnotations.GetInstance,
    instance_component: InstanceComponentAnnotations.GetInstanceComponent,
):
    return instance_component


@router.post(
    "",
    summary="Instance Component Add",
    status_code=status.HTTP_201_CREATED,
    dependencies=[InstanceDepends.InstanceMaintainer],
)
def components_add(
    *,
    instance_component_service: InstanceComponentAnnotations.InstanceComponentService,
    instance: InstanceAnnotations.GetInstance,
    component_in: InstanceComponentCreate,
):
    return instance_component_service.add(
        instance=instance,
        component_in=component_in,
    )


@router.delete(
    "/{component_id}",
    summary="Instance Component Remove",
    status_code=status.HTTP_204_NO_CONTENT,
)
def components_remove(
    *,
    instance_component_service: InstanceComponentAnnotations.InstanceComponentService,
    instance: InstanceAnnotations.GetInstance,
    instance_component: InstanceComponentAnnotations.GetInstanceComponent,
):
    return instance_component_service.remove(instance_component=instance_component)
