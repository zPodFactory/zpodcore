from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from zpodapi.lib import dependencies
from zpodcommon import models as M

from . import instance_dependencies, instance_services
from .instance_schemas import (
    InstanceComponentView,
    InstanceCreate,
    InstanceUpdate,
    InstanceView,
)

router = APIRouter(
    tags=["instances"],
    dependencies=[Depends(dependencies.get_current_user_and_update)],
)


@router.get(
    "/instances",
    response_model=list[InstanceView],
)
def get_all(
    *,
    session: Session = Depends(dependencies.get_session),
    name: str | None = None,
):
    return instance_services.get_all(session, name=name)


@router.get(
    "/instances/{id}",
    response_model=InstanceView,
)
def get(
    *,
    instance: M.Instance = Depends(instance_dependencies.get_instance_record),
):
    return instance


@router.post(
    "/instances",
    response_model=InstanceView,
    status_code=status.HTTP_201_CREATED,
)
def create(
    *,
    session: Session = Depends(dependencies.get_session),
    current_user: M.User = Depends(dependencies.get_current_user_and_update),
    instance_in: InstanceCreate,
):
    if instance_services.get_all(
        session=session,
        name=instance_in.name,
    ):
        raise HTTPException(status_code=422, detail="Conflicting record found")
    return instance_services.create(
        session=session,
        current_user=current_user,
        instance_in=instance_in,
    )


@router.patch(
    "/instances/{id}",
    response_model=InstanceView,
    status_code=status.HTTP_201_CREATED,
)
def update(
    *,
    session: Session = Depends(dependencies.get_session),
    instance: M.Instance = Depends(instance_dependencies.get_instance_record),
    instance_in: InstanceUpdate,
):
    return instance_services.update(
        session=session,
        instance=instance,
        instance_in=instance_in,
    )


@router.delete(
    "/instances/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    *,
    session: Session = Depends(dependencies.get_session),
    instance: M.Instance = Depends(instance_dependencies.get_instance_record),
):
    return instance_services.delete(session=session, instance=instance)


@router.get(
    "/instances/{id}/components",
    response_model=list[InstanceComponentView],
)
def components_get_all(
    *,
    session: Session = Depends(dependencies.get_session),
    instance: M.Instance = Depends(instance_dependencies.get_instance_record),
):
    return instance_services.components_get_all(session, instance=instance)
