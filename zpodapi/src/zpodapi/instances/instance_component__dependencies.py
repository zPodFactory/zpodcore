from typing import Annotated

from fastapi import Depends, HTTPException, Path, status

from zpodapi.lib.global_dependencies import service_init_annotation
from zpodapi.lib.id_types import IdValidator
from zpodcommon import models as M

from .instance__dependencies import InstanceAnnotations
from .instance_component__services import InstanceComponentService

IdHostnameType = Annotated[
    str,
    IdValidator(
        fields={"id": int, "hostname": str},
    ),
]


def get_instance_component(
    *,
    instance_component_service: "InstanceComponentAnnotations.InstanceComponentService",
    instance: InstanceAnnotations.GetInstance,
    component_id: Annotated[
        IdHostnameType,
        Path(
            openapi_examples={
                "id": {"value": "1"},
                "hostname": {"value": "hostname=esxi11"},
            },
        ),
    ],
):
    if instance_component := instance_component_service.crud.get(
        **component_id,
        where_extra=[M.InstanceComponent.instance_id == instance.id],
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
