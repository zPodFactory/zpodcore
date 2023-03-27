from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from zpodapi.lib import dependencies
from zpodapi.lib.route_logger import RouteLogger
from zpodcommon import models as M

from . import component__dependencies
from .component__schemas import ComponentViewFull
from .component__services import ComponentService

router = APIRouter(
    prefix="/components",
    tags=["components"],
    dependencies=[Depends(dependencies.get_current_user_and_update)],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[ComponentViewFull],
)
def get_all(
    *,
    session: Session = Depends(dependencies.get_session),
):
    return ComponentService(session=session).get_all()


@router.get("/{component_uid}", response_model=ComponentViewFull)
def get(
    *,
    component: M.Component = Depends(component__dependencies.get_component_record),
):
    return component


@router.put(
    "/{component_uid}/enable",
    response_model=ComponentViewFull,
    status_code=status.HTTP_201_CREATED,
)
def enable(
    *,
    session: Session = Depends(dependencies.get_session),
    component: M.Component = Depends(component__dependencies.get_component_record),
):
    return ComponentService(session=session).enable(component=component)


@router.put(
    "/{component_uid}/disable",
    response_model=ComponentViewFull,
    status_code=status.HTTP_201_CREATED,
)
def disable(
    *,
    session: Session = Depends(dependencies.get_session),
    component: M.Component = Depends(component__dependencies.get_component_record),
):
    return ComponentService(session=session).disable(component=component)
