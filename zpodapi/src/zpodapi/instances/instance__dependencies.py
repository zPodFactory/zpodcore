from typing import Annotated

from fastapi import Depends, HTTPException, Path, status

from zpodapi.lib.global_dependencies import service_init_annotation
from zpodapi.lib.id_types import IdNameType
from zpodcommon import models as M
from zpodcommon.enums import InstancePermission

from .instance__services import InstanceService


def get_instance(
    *,
    instance_service: "InstanceAnnotations.InstanceService",
    id: Annotated[
        IdNameType,
        Path(
            openapi_examples={
                "id": {"value": "1"},
                "name": {"value": "name=tanzu-lab"},
            },
        ),
    ],
):
    if instance := instance_service.get(**id):
        return instance
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Instance not found",
    )


def get_user_instance_permissions(
    *,
    instance: "InstanceAnnotations.GetInstance",
    instance_service: "InstanceAnnotations.InstanceService",
):
    user_id = instance_service.current_user.id
    user_permissions = set()

    # Add ADMIN, if superadmin
    if instance_service.current_user.superadmin:
        user_permissions.add(InstancePermission.ADMIN)

    for permission in instance.permissions:
        if user_id in [u.id for u in permission.users]:
            user_permissions.add(permission.permission)
            continue
        for pg in permission.permission_groups:
            if user_id in [u.id for u in pg.users]:
                user_permissions.add(permission.permission)
                break
    return user_permissions


def instance_maintainer(
    *,
    instance_user_permissions: "InstanceAnnotations.GetUserInstancePermissions",
):
    if not instance_user_permissions.intersection(
        {
            InstancePermission.OWNER,
            InstancePermission.ADMIN,
        }
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Insufficient permission on instance",
        )


def instance_reader(
    *,
    instance_user_permissions: "InstanceAnnotations.GetUserInstancePermissions",
):
    if not instance_user_permissions.intersection(
        {
            InstancePermission.OWNER,
            InstancePermission.ADMIN,
            InstancePermission.USER,
        }
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Insufficient permission on instance",
        )


class InstanceDepends:
    InstanceMaintainer = Depends(instance_maintainer)
    InstanceReader = Depends(instance_reader)


class InstanceAnnotations:
    InstanceService = service_init_annotation(InstanceService)
    GetInstance = Annotated[
        M.Instance,
        Depends(get_instance),
    ]
    GetUserInstancePermissions = Annotated[
        set[InstancePermission],
        Depends(get_user_instance_permissions),
    ]
