from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from zpodapi.lib import dependencies
from zpodapi.lib.route_logger import RouteLogger

from . import component__services
from .component__schemas import ComponentUpdate, ComponentViewFull

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
    return component__services.get_all(session)


@router.get("/{component_uid}", response_model=ComponentViewFull)
def get(
    *,
    component_uid: str,
    session: Session = Depends(dependencies.get_session),
):
    return component__services.get(
        session=session, component_in=ComponentUpdate(component_uid=component_uid)
    )


@router.put(
    "/{component_uid}/enable",
    response_model=ComponentViewFull,
    status_code=status.HTTP_201_CREATED,
)
def enable(
    *,
    session: Session = Depends(dependencies.get_session),
    component_uid: str,
):
    return component__services.enable(
        session=session, component_in=ComponentUpdate(component_uid=component_uid)
    )


@router.put(
    "/{component_uid}/disable",
    response_model=ComponentViewFull,
    status_code=status.HTTP_201_CREATED,
)
def disable(
    *,
    session: Session = Depends(dependencies.get_session),
    component_uid: str,
):
    return component__services.disable(
        session=session, component_in=ComponentUpdate(component_uid=component_uid)
    )
