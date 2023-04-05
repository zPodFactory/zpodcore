from typing import Annotated

from fastapi import Depends, HTTPException, Path

from zpodapi.lib.global_dependencies import service_init_annotation
from zpodcommon import models as M

from .instance__services import InstanceService
from .instance__types import InstanceIdType


def get_instance(
    *,
    instance_service: "InstanceAnnotations.InstanceService",
    id: Annotated[
        InstanceIdType,
        Path(
            examples={
                "id": {"value": "1"},
                "name": {"value": "name=tanzu-lab"},
            },
        ),
    ],
):
    if instance := instance_service.get(**InstanceIdType.args(id)):
        return instance
    raise HTTPException(status_code=404, detail="Instance not found")


class InstanceDepends:
    pass


class InstanceAnnotations:
    GetInstance = Annotated[M.Instance, Depends(get_instance)]
    InstanceService = service_init_annotation(InstanceService)
