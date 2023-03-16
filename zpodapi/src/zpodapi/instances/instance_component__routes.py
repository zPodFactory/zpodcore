from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from zpodapi.lib import dependencies
from zpodcommon import models as M

from . import instance__dependencies
from .instance_component__schemas import InstanceComponentCreate, InstanceComponentView
from .instance_component__services import InstanceComponentService

router = APIRouter(
    prefix="/instances/{id}/components",
    tags=["instances"],
    dependencies=[Depends(dependencies.get_current_user_and_update)],
)


@router.get(
    "",
    response_model=list[InstanceComponentView],
)
def components_get_all(
    *,
    instance: M.Instance = Depends(instance__dependencies.get_instance_record),
):
    return instance.components


@router.post(
    "",
    response_model=InstanceComponentView,
    status_code=status.HTTP_201_CREATED,
)
def components_add(
    *,
    session: Session = Depends(dependencies.get_session),
    instance: M.Instance = Depends(instance__dependencies.get_instance_record),
    component_in: InstanceComponentCreate,
):
    return InstanceComponentService(session=session).create(
        item_in=M.InstanceComponent(
            instance_id=instance.id,
            component_uid=component_in.component_uid,
        )
    )


@router.delete(
    "/{component_uid}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def components_delete(
    *,
    session: Session = Depends(dependencies.get_session),
    instance: M.Instance = Depends(instance__dependencies.get_instance_record),
    component_uid: str,
):
    service = InstanceComponentService(session=session)
    instance_component = service.get(
        instance_id=instance.id, component_uid=component_uid
    )
    service.delete(item=instance_component)
