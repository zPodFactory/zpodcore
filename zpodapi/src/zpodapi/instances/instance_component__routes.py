from fastapi import APIRouter, status

from zpodapi.lib.global_dependencies import GlobalDepends

from .instance__dependencies import InstanceAnnotations
from .instance_component__dependencies import InstanceComponentAnnotations
from .instance_component__schemas import InstanceComponentCreate, InstanceComponentView

router = APIRouter(
    prefix="/instances/{id}/components",
    tags=["instances"],
    dependencies=[GlobalDepends.UpdateLastConnectionDate],
)


@router.get(
    "",
    response_model=list[InstanceComponentView],
)
def components_get_all(
    *,
    instance: InstanceAnnotations.GetInstance,
):
    return instance.components


@router.post(
    "",
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
#     status_code=status.HTTP_204_NO_CONTENT,
# )
# def components_delete(
#     *,
#     instance_component_service: InstanceComponentAnnotations.InstanceComponentService,
#     instance: InstanceComponentAnnotations.GetInstance,
#     component_uid: str,
# ):
#     instance_component = instance_component_service.get(
#         instance_id=instance.id, component_uid=component_uid
#     )
#     instance_component_service.delete(item=instance_component)
