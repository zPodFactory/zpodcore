from typing import Annotated

from fastapi import Depends, HTTPException, Path, status

from zpodapi.lib.global_dependencies import service_init_annotation
from zpodcommon import models as M
from zpodcommon.enums import InstancePermission

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
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Instance not found",
    )


def get_user_instance_permissions(
    *,
    instance: "InstanceAnnotations.GetInstance",
    instance_service: "InstanceAnnotations.InstanceService",
):
    return instance_service.get_user_instance_permissions(instance.id)


def is_instance_admin(
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


def is_instance_readable(
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
    IsInstanceAdmin = Depends(is_instance_admin)
    IsInstanceReadable = Depends(is_instance_readable)


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
