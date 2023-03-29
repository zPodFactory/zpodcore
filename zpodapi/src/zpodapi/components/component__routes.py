from fastapi import APIRouter, status

from zpodapi.lib import dependencies
from zpodapi.lib.route_logger import RouteLogger

from . import component__dependencies
from .component__schemas import ComponentViewFull
from .component__services import ComponentService

router = APIRouter(
    prefix="/components",
    tags=["components"],
    dependencies=[dependencies.UpdateLastConnectionDateDepends],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[ComponentViewFull],
)
def get_all(
    *,
    session: dependencies.GetSession,
):
    return ComponentService(session=session).get_all()


@router.get(
    "/{component_uid}",
    response_model=ComponentViewFull,
)
def get(
    *,
    component: component__dependencies.GetComponentRecord,
):
    return component


@router.put(
    "/{component_uid}/enable",
    response_model=ComponentViewFull,
    status_code=status.HTTP_201_CREATED,
)
def enable(
    *,
    session: dependencies.GetSession,
    component: component__dependencies.GetComponentRecord,
):
    return ComponentService(session=session).enable(component=component)


@router.put(
    "/{component_uid}/disable",
    response_model=ComponentViewFull,
    status_code=status.HTTP_201_CREATED,
)
def disable(
    *,
    session: dependencies.GetSession,
    component: component__dependencies.GetComponentRecord,
):
    return ComponentService(session=session).disable(component=component)
