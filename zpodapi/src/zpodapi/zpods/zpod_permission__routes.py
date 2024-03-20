from fastapi import APIRouter, status

from zpodapi.users.user__schemas import UserView
from zpodcommon.enums import ZpodPermission

from ..permission_groups.permission_group__dependencies import (
    PermissionGroupAnnotations,
)
from ..users.user__dependencies import UserAnnotations
from .zpod__dependencies import ZpodAnnotations, ZpodDepends
from .zpod_permission__dependencies import ZpodPermissionAnnotations
from .zpod_permission__schemas import (
    ZpodPermissionGroupAddRemove,
    ZpodPermissionUserAddRemove,
    ZpodPermissionView,
)

router = APIRouter(
    prefix="/zpods/{id}/permissions",
    tags=["zpods"],
)


@router.get(
    "",
    summary="zPod Permission Get All",
    response_model=list[ZpodPermissionView],
)
def permissions_get_all(
    *,
    zpod: ZpodAnnotations.GetZpod,
):
    return zpod.permissions


@router.post(
    "/{permission}/users",
    summary="zPod Permission User Add",
    status_code=status.HTTP_201_CREATED,
    response_model=list[UserView],
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def permissions_users_add(
    zpod_permission_service: ZpodPermissionAnnotations.ZpodPermissionService,
    user_service: UserAnnotations.UserService,
    permission: ZpodPermission,
    zpod: ZpodAnnotations.GetZpod,
    permission_user_in: ZpodPermissionUserAddRemove,
):
    user = user_service.get_user_record(
        user_id=permission_user_in.user_id,
        username=permission_user_in.username,
    )
    return zpod_permission_service.user_add(
        zpod=zpod,
        permission=permission,
        user=user,
    )


@router.delete(
    "/{permission}/users",
    summary="zPod Permission User Remove",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def permissions_users_remove(
    zpod_permission_service: ZpodPermissionAnnotations.ZpodPermissionService,
    user_service: UserAnnotations.UserService,
    permission: ZpodPermission,
    zpod: ZpodAnnotations.GetZpod,
    permission_user_in: ZpodPermissionUserAddRemove,
):
    user = user_service.get_user_record(
        user_id=permission_user_in.user_id,
        username=permission_user_in.username,
    )
    return zpod_permission_service.user_remove(
        zpod=zpod,
        permission=permission,
        user=user,
    )


@router.post(
    "/{permission}/groups",
    summary="zPod Permission Group Add",
    status_code=status.HTTP_201_CREATED,
    response_model=list[UserView],
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def permissions_groups_add(
    zpod_permission_service: ZpodPermissionAnnotations.ZpodPermissionService,
    permission_group_service: PermissionGroupAnnotations.PermissionGroupService,
    permission: ZpodPermission,
    zpod: ZpodAnnotations.GetZpod,
    permission_group_in: ZpodPermissionGroupAddRemove,
):
    group = permission_group_service.get_permission_group_record(
        group_id=permission_group_in.group_id,
        groupname=permission_group_in.groupname,
    )
    return zpod_permission_service.group_add(
        zpod=zpod,
        permission=permission,
        group=group,
    )


@router.delete(
    "/{permission}/groups",
    summary="zPod Permission Group Remove",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def permissions_groups_remove(
    zpod_permission_service: ZpodPermissionAnnotations.ZpodPermissionService,
    permission_group_service: PermissionGroupAnnotations.PermissionGroupService,
    permission: ZpodPermission,
    zpod: ZpodAnnotations.GetZpod,
    permission_group_in: ZpodPermissionGroupAddRemove,
):
    group = permission_group_service.get_permission_group_record(
        group_id=permission_group_in.group_id,
        groupname=permission_group_in.groupname,
    )
    return zpod_permission_service.group_remove(
        zpode=zpod,
        permission=permission,
        group=group,
    )
