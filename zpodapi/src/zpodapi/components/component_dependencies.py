from fastapi import Depends, HTTPException
from sqlmodel import Session

from zpodapi.lib import dependencies

from . import component_services
from .component_schemas import ComponentUpdate


def get_component_record(
    *,
    session: Session = Depends(dependencies.get_session),
    component_in: ComponentUpdate,
):
    if component := component_services.get(session=session, component_in=component_in):
        return component
    raise HTTPException(status_code=404, detail="Component not found")
