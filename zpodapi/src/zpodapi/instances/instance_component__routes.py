from fastapi import APIRouter, status

from zpodapi.lib.global_dependencies import GlobalAnnotations, GlobalDepends

from .instance__dependencies import InstanceAnnotations
from .instance_component__schemas import InstanceComponentCreate, InstanceComponentView
from .instance_component__services import InstanceComponentService

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
    session: GlobalAnnotations.GetSession,
    instance: InstanceAnnotations.GetInstance,
    component_in: InstanceComponentCreate,
):
    return InstanceComponentService(session=session).add(
        instance_id=instance.id,
        component_uid=component_in.component_uid,
    )


# @router.delete(
#     "/{component_uid}",
#     status_code=status.HTTP_204_NO_CONTENT,
# )
# def components_delete(
#     *,
#     session: GlobalAnnotations.GetSession,
#     instance: M.Instance = InstanceAnnotations.GetInstance,
#     component_uid: str,
# ):
#     service = InstanceComponentService(session=session)
#     instance_component = service.get(
#         instance_id=instance.id, component_uid=component_uid
#     )
#     service.delete(item=instance_component)
