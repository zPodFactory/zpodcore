from fastapi import APIRouter, status

from .instance__dependencies import InstanceAnnotations
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
)
def components_get_all(
    *,
    instance: InstanceAnnotations.GetInstance,
):
    return instance.components


@router.post(
    "",
    summary="Instance Component Add",
    response_model=InstanceComponentView,
    status_code=status.HTTP_201_CREATED,
)
def components_add(
    *,
    instance_component_service: InstanceComponentAnnotations.InstanceComponentService,
    instance: InstanceAnnotations.GetInstance,
    component_in: InstanceComponentCreate,
):
    return instance_component_service.add(
        instance_id=instance.id,
        component_uid=component_in.component_uid,
    )


# @router.delete(
#     "/{component_uid}",
#     summary="Instance Component Delete",
#     status_code=status.HTTP_204_NO_CONTENT,
# )
# def components_delete(
#     *,
#     instance_component_service: InstanceComponentAnnotations.InstanceComponentService,
#     instance: InstanceComponentAnnotations.GetInstance,
#     component_uid: str,
# ):
#     instance_component = instance_component_service.crud.get(
#         id=instance.id, component_uid=component_uid
#     )
#     instance_component_service.crud.delete(item=instance_component)
