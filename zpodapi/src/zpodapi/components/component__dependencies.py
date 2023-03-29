from typing import Annotated

from fastapi import Depends, HTTPException

from zpodapi.lib.global_dependencies import GlobalAnnotations
from zpodcommon import models as M

from .component__services import ComponentService


def get_component(
    *,
    session: GlobalAnnotations.GetSession,
    component_uid: str,
):
    if component := ComponentService(session=session).get(value=component_uid):
        return component
    raise HTTPException(status_code=404, detail="Component not found")


class ComponentDepends:
    GetComponent = Depends(get_component)


class ComponentAnnotations:
    GetComponent = Annotated[M.Component, ComponentDepends.GetComponent]
