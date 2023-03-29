from fastapi import APIRouter, HTTPException, status

from zpodapi.lib import dependencies
from zpodapi.lib.route_logger import RouteLogger

from . import instance__dependencies
from .instance__schemas import InstanceCreate, InstanceUpdate, InstanceView
from .instance__services import InstanceService

router = APIRouter(
    prefix="/instances",
    tags=["instances"],
    dependencies=[dependencies.UpdateLastConnectionDateDepends],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[InstanceView],
)
def get_all(
    *,
    session: dependencies.GetSession,
    name: str | None = None,
):
    return InstanceService(session=session).get_all(name=name)


@router.get(
    "/{id}",
    response_model=InstanceView,
)
def get(
    *,
    instance: instance__dependencies.GetInstance,
):
    return instance


@router.post(
    "",
    response_model=InstanceView,
    status_code=status.HTTP_201_CREATED,
)
def create(
    *,
    session: dependencies.GetSession,
    current_user: dependencies.GetCurrentUser,
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
    session: dependencies.GetSession,
    instance: instance__dependencies.GetInstance,
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
    session: dependencies.GetSession,
    instance: instance__dependencies.GetInstance,
):
    return InstanceService(session=session).delete(item=instance)
