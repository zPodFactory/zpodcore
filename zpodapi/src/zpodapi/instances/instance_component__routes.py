from fastapi import APIRouter, status

from zpodapi.lib import dependencies
from zpodcommon import models as M

from . import instance__dependencies
from .instance_component__schemas import InstanceComponentCreate, InstanceComponentView
from .instance_component__services import InstanceComponentService

router = APIRouter(
    prefix="/instances/{id}/components",
    tags=["instances"],
    dependencies=[dependencies.GetCurrentUserAndUpdateDepends],
)


@router.get(
    "",
    response_model=list[InstanceComponentView],
)
def components_get_all(
    *,
    instance: instance__dependencies.GetInstanceRecord,
):
    return instance.components


@router.post(
    "",
    response_model=InstanceComponentView,
    status_code=status.HTTP_201_CREATED,
)
def components_add(
    *,
    session: dependencies.GetSession,
    instance: instance__dependencies.GetInstanceRecord,
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
#     session: dependencies.GetSession,
#     instance: M.Instance = instance__dependencies.GetInstanceRecord,
#     component_uid: str,
# ):
#     service = InstanceComponentService(session=session)
#     instance_component = service.get(
#         instance_id=instance.id, component_uid=component_uid
#     )
#     service.delete(item=instance_component)
