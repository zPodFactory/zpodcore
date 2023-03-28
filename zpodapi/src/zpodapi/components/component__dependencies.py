from typing import Annotated

from fastapi import Depends, HTTPException

from zpodapi.lib import dependencies
from zpodcommon import models as M

from .component__services import ComponentService


def get_component_record(
    *,
    session: dependencies.GetSession,
    component_uid: str,
):
    if component := ComponentService(session=session).get(value=component_uid):
        return component
    raise HTTPException(status_code=404, detail="Component not found")


GetComponentRecordDepends = Depends(get_component_record)
GetComponentRecord = Annotated[M.Component, GetComponentRecordDepends]
