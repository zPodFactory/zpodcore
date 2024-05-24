from typing import Annotated

from fastapi import Depends, HTTPException, Path, status

from zpodapi.lib.global_dependencies import service_init_annotation
from zpodapi.lib.types import IdNameType
from zpodcommon import models as M
from zpodcommon.enums import ZpodPermission

from .zpod__services import ZpodService


def get_zpod(
    *,
    zpod_service: "ZpodAnnotations.ZpodService",
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
    if zpod := zpod_service.get(**id):
        return zpod
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="zPod not found",
    )


def get_user_zpod_permissions(
    *,
    zpod: "ZpodAnnotations.GetZpod",
    zpod_service: "ZpodAnnotations.ZpodService",
):
    user_id = zpod_service.current_user.id
    user_permissions = set()

    # Add ADMIN, if superadmin
    if zpod_service.current_user.superadmin:
        user_permissions.add(ZpodPermission.ADMIN)

    for permission in zpod.permissions:
        if user_id in [u.id for u in permission.users]:
            user_permissions.add(permission.permission)
            continue
        for pg in permission.permission_groups:
            if user_id in [u.id for u in pg.users]:
                user_permissions.add(permission.permission)
                break
    return user_permissions


def zpod_maintainer(
    *,
    zpod_user_permissions: "ZpodAnnotations.GetUserZpodPermissions",
):
    if not zpod_user_permissions.intersection(
        {
            ZpodPermission.OWNER,
            ZpodPermission.ADMIN,
        }
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Insufficient permission on zPod",
        )


def zpod_reader(
    *,
    zpod_user_permissions: "ZpodAnnotations.GetUserZpodPermissions",
):
    if not zpod_user_permissions.intersection(
        {
            ZpodPermission.OWNER,
            ZpodPermission.ADMIN,
            ZpodPermission.USER,
        }
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Insufficient permission on zPod",
        )


class ZpodDepends:
    ZpodMaintainer = Depends(zpod_maintainer)
    ZpodReader = Depends(zpod_reader)


class ZpodAnnotations:
    ZpodService = service_init_annotation(ZpodService)
    GetZpod = Annotated[
        M.Zpod,
        Depends(get_zpod),
    ]
    GetUserZpodPermissions = Annotated[
        set[ZpodPermission],
        Depends(get_user_zpod_permissions),
    ]
