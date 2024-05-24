from typing import Annotated

from fastapi import Depends, HTTPException, Path, status

from zpodapi.lib.global_dependencies import service_init_annotation
from zpodapi.lib.types import IdValidator
from zpodcommon import models as M

from .zpod__dependencies import ZpodAnnotations
from .zpod_component__services import ZpodComponentService

IdHostnameType = Annotated[
    str,
    IdValidator(
        fields={"id": int, "hostname": str},
    ),
]


def get_zpod_component(
    *,
    zpod_component_service: "ZpodComponentAnnotations.ZpodComponentService",
    zpod: ZpodAnnotations.GetZpod,
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
    if zpod_component := zpod_component_service.crud.get(
        **component_id,
        where_extra=[M.ZpodComponent.zpod_id == zpod.id],
    ):
        return zpod_component
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="zPod component not found",
    )


class ZpodComponentDepends:
    pass


class ZpodComponentAnnotations:
    ZpodComponentService = service_init_annotation(ZpodComponentService)
    GetZpodComponent = Annotated[
        M.ZpodComponent,
        Depends(get_zpod_component),
    ]
