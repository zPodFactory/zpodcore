from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from zpodapi.lib import dependencies
from zpodapi.lib.route_logger import RouteLogger

from . import component_services
from .component_schemas import ComponentUpdate, ComponentViewFull

router = APIRouter(
    tags=["components"],
    dependencies=[Depends(dependencies.get_current_user_and_update)],
    route_class=RouteLogger,
)


@router.get(
    "/components",
    response_model=list[ComponentViewFull],
)
def get_all(
    *,
    session: Session = Depends(dependencies.get_session),
):
    return component_services.get_all(session)


@router.get("/components/{component_uid}", response_model=ComponentViewFull)
def get(
    *,
    component_uid: str,
    session: Session = Depends(dependencies.get_session),
):
    return component_services.get(
        session=session, component_in=ComponentUpdate(component_uid=component_uid)
    )


@router.put(
    "/components/{component_uid}/enable",
    response_model=ComponentViewFull,
    status_code=status.HTTP_201_CREATED,
)
def enable(
    *,
    session: Session = Depends(dependencies.get_session),
    component_uid: str,
):
    return component_services.enable(
        session=session, component_in=ComponentUpdate(component_uid=component_uid)
    )


@router.put(
    "/components/{component_uid}/disable",
    response_model=ComponentViewFull,
    status_code=status.HTTP_201_CREATED,
)
def disable(
    *,
    session: Session = Depends(dependencies.get_session),
    component_uid: str,
):
    return component_services.disable(
        session=session, component_in=ComponentUpdate(component_uid=component_uid)
    )
