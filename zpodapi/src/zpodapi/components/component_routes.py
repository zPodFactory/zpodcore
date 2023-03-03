from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from zpodapi.lib import dependencies
from zpodcommon import models as M

from . import component_dependencies, component_services
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


@router.patch(
    "/components/{action}",
    response_model=ComponentView,
    status_code=status.HTTP_201_CREATED,
)
def change_component_state(
    *,
    session: Session = Depends(dependencies.get_session),
    component: M.Component = Depends(component_dependencies.get_component_record),
    component_in: ComponentUpdate,
    action: str,
):
    return component_services.update(
        session=session,
        component=component,
        component_in=component_in,
        filename=filename,
    )
