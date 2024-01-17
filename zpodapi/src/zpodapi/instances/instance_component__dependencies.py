from typing import Annotated

from fastapi import Depends, HTTPException, Path, status

from zpodapi.lib.global_dependencies import service_init_annotation
from zpodcommon import models as M

from .instance_component__services import InstanceComponentService
from .instance_component__types import InstanceComponentIdType


def get_instance_component(
    *,
    instance_component_service: "InstanceComponentAnnotations.InstanceComponentService",
    component_id: Annotated[
        InstanceComponentIdType,
        Path(
            examples={
                "id": {"value": "1"},
                "hostname": {"value": "hostname=esxi11"},
            },
        ),
    ],
):
    if instance_component := instance_component_service.crud.get(
        **InstanceComponentIdType.args(component_id)
    ):
        return instance_component
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Instance component not found",
    )


class InstanceComponentDepends:
    pass


class InstanceComponentAnnotations:
    InstanceComponentService = service_init_annotation(InstanceComponentService)
    GetInstanceComponent = Annotated[
        M.InstanceComponent,
        Depends(get_instance_component),
    ]
