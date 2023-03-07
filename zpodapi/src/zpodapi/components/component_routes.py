from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from zpodapi.lib import dependencies
from zpodcommon import models as M

from . import  component_services
from .component_schemas import ComponentUpdate, ComponentView

router = APIRouter(
    tags=["components"],
    dependencies=[Depends(dependencies.get_current_user_and_update)],
)


@router.get(
    "/components",
    response_model=list[ComponentView],
)
def get_all(
    *,
    session: Session = Depends(dependencies.get_session),
):
    return component_services.get_all(session)


@router.get("/components/{component_uid}", response_model=ComponentView)
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
    response_model=ComponentView,
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
    response_model=ComponentView,
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
