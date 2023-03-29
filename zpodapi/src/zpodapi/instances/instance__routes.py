from fastapi import APIRouter, HTTPException, status

from zpodapi.lib.global_dependencies import GlobalAnnotations, GlobalDepends
from zpodapi.lib.route_logger import RouteLogger

from .instance__dependencies import InstanceAnnotations
from .instance__schemas import InstanceCreate, InstanceUpdate, InstanceView
from .instance__services import InstanceService

router = APIRouter(
    prefix="/instances",
    tags=["instances"],
    dependencies=[GlobalDepends.UpdateLastConnectionDate],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[InstanceView],
)
def get_all(
    *,
    session: GlobalAnnotations.GetSession,
    name: str | None = None,
):
    return InstanceService(session=session).get_all(name=name)


@router.get(
    "/{id}",
    response_model=InstanceView,
)
def get(
    *,
    instance: InstanceAnnotations.GetInstance,
):
    return instance


@router.post(
    "",
    response_model=InstanceView,
    status_code=status.HTTP_201_CREATED,
)
def create(
    *,
    session: GlobalAnnotations.GetSession,
    current_user: GlobalAnnotations.GetCurrentUser,
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
    session: GlobalAnnotations.GetSession,
    instance: InstanceAnnotations.GetInstance,
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
    session: GlobalAnnotations.GetSession,
    instance: InstanceAnnotations.GetInstance,
):
    return InstanceService(session=session).delete(item=instance)
