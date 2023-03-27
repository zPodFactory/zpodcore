from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from zpodapi.lib import dependencies
from zpodcommon import models as M

from . import instance__dependencies
from .instance__schemas import InstanceCreate, InstanceUpdate, InstanceView
from .instance__services import InstanceService

router = APIRouter(
    prefix="/instances",
    tags=["instances"],
    dependencies=[Depends(dependencies.get_current_user_and_update)],
)


@router.get(
    "",
    response_model=list[InstanceView],
)
def get_all(
    *,
    session: Session = Depends(dependencies.get_session),
    name: str | None = None,
):
    return InstanceService(session=session).get_all(name=name)


@router.get(
    "/{id}",
    response_model=InstanceView,
)
def get(
    *,
    instance: M.Instance = Depends(instance__dependencies.get_instance_record),
):
    return instance


@router.post(
    "",
    response_model=InstanceView,
    status_code=status.HTTP_201_CREATED,
)
def create(
    *,
    session: Session = Depends(dependencies.get_session),
    current_user: M.User = Depends(dependencies.get_current_user_and_update),
    instance_in: InstanceCreate,
):
    service = InstanceService(session=session)
    if service.get_all(name=instance_in.name):
        raise HTTPException(status_code=422, detail="Conflicting record found")
    return service.create(current_user=current_user, item_in=instance_in)


@router.patch(
    "/{id}",
    response_model=InstanceView,
    status_code=status.HTTP_201_CREATED,
)
def update(
    *,
    session: Session = Depends(dependencies.get_session),
    instance: M.Instance = Depends(instance__dependencies.get_instance_record),
    instance_in: InstanceUpdate,
):
    return InstanceService(session=session).update(
        item=instance,
        item_in=instance_in,
    )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    *,
    session: Session = Depends(dependencies.get_session),
    instance: M.Instance = Depends(instance__dependencies.get_instance_record),
):
    return InstanceService(session=session).delete(item=instance)
