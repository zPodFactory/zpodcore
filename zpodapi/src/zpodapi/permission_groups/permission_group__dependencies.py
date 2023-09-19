from typing import Annotated

from fastapi import Depends, HTTPException, Path

from zpodapi.lib.global_dependencies import service_init_annotation
from zpodcommon import models as M

from .permission_group__services import PermissionGroupService
from .permission_group__types import PermissionGroupIdType


def get_permission_group(
    *,
    permission_group_service: "PermissionGroupAnnotations.PermissionGroupService",
    id: Annotated[
        PermissionGroupIdType,
        Path(
            examples={
                "id": {"value": "1"},
                "name": {"value": "name=admins"},
            },
        ),
    ],
):
    if permission_group := permission_group_service.crud.get(
        **PermissionGroupIdType.args(id)
    ):
        return permission_group
    raise HTTPException(status_code=404, detail="Permission Group not found")


class PermissionGroupDepends:
    pass


class PermissionGroupAnnotations:
    GetPermissionGroup = Annotated[M.PermissionGroup, Depends(get_permission_group)]
    PermissionGroupService = service_init_annotation(PermissionGroupService)
