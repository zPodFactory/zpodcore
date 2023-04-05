from typing import Annotated

from fastapi import Depends, HTTPException, Path

from zpodapi.lib.global_dependencies import service_init_annotation
from zpodcommon import models as M

from .component__services import ComponentService
from .component__types import ComponentIdType


def get_component(
    *,
    component_service: "ComponentAnnotations.ComponentService",
    id: Annotated[
        ComponentIdType,
        Path(
            examples={
                "id": {"value": "1"},
                "uid": {"value": "uid=vcda-4.4.1"},
            },
        ),
    ],
):
    if component := component_service.get(value=id):
        return component
    raise HTTPException(status_code=404, detail="Component not found")


class ComponentDepends:
    pass


class ComponentAnnotations:
    GetComponent = Annotated[M.Component, Depends(get_component)]
    ComponentService = service_init_annotation(ComponentService)
