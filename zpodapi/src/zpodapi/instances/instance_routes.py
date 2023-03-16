from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from zpodapi.lib import dependencies
from zpodcommon import models as M

from . import instance_dependencies
from .instance_schemas import (
    InstanceComponentCreate,
    InstanceComponentView,
    InstanceCreate,
    InstanceFeatureView,
    InstanceNetworkView,
    InstanceUpdate,
    InstanceView,
)
from .instance_services import InstanceComponentService, InstanceService

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
    return InstanceService(session=session).get_all(name=name)


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
    service = InstanceService(session=session)
    if service.get_all(
        name=instance_in.name,
    ):
        raise HTTPException(status_code=422, detail="Conflicting record found")
    return service.create(
        current_user=current_user,
        item_in=instance_in,
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
    return InstanceService(session=session).update(
        item=instance,
        item_in=instance_in,
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
    return InstanceService(session=session).update(item=instance)


@router.get(
    "/instances/{id}/components",
    response_model=list[InstanceComponentView],
)
def components_get_all(
    *,
    instance: M.Instance = Depends(instance_dependencies.get_instance_record),
):
    return instance.components


@router.post(
    "/instances/{id}/components",
    response_model=InstanceComponentView,
    status_code=status.HTTP_201_CREATED,
)
def components_add(
    *,
    session: Session = Depends(dependencies.get_session),
    instance: M.Instance = Depends(instance_dependencies.get_instance_record),
    component_in: InstanceComponentCreate,
):
    return InstanceComponentService(session=session).create(
        item_in=M.InstanceComponent(
            instance_id=instance.id,
            component_uid=component_in.component_uid,
        )
    )


@router.delete(
    "/instances/{id}/components/{component_uid}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def components_delete(
    *,
    session: Session = Depends(dependencies.get_session),
    instance: M.Instance = Depends(instance_dependencies.get_instance_record),
    component_uid: str,
):
    service = InstanceComponentService(session=session)
    instance_component = service.get(
        instance_id=instance.id, component_uid=component_uid
    )
    service.delete(item=instance_component)


@router.get(
    "/instances/{id}/features",
    response_model=list[InstanceFeatureView],
)
def features_get_all(
    *,
    instance: M.Instance = Depends(instance_dependencies.get_instance_record),
):
    return instance.features


@router.get(
    "/instances/{id}/networks",
    response_model=list[InstanceNetworkView],
)
def networks_get_all(
    *,
    instance: M.Instance = Depends(instance_dependencies.get_instance_record),
):
    return instance.networks
