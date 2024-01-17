from fastapi import APIRouter, status

from zpodapi.users.user__schemas import UserView
from zpodcommon.enums import InstancePermission

from ..permission_groups.permission_group__dependencies import (
    PermissionGroupAnnotations,
)
from ..users.user__dependencies import UserAnnotations
from .instance__dependencies import InstanceAnnotations, InstanceDepends
from .instance_permission__dependencies import InstancePermissionAnnotations
from .instance_permission__schemas import (
    InstancePermissionGroupAddRemove,
    InstancePermissionUserAddRemove,
    InstancePermissionView,
)

router = APIRouter(
    prefix="/instances/{id}/permissions",
    tags=["instances"],
)


@router.get(
    "",
    summary="Instance Permission Get All",
    response_model=list[InstancePermissionView],
)
def permissions_get_all(
    *,
    instance: InstanceAnnotations.GetInstance,
):
    return instance.permissions


@router.post(
    "/{permission}/users",
    summary="Instance Permission User Add",
    status_code=status.HTTP_201_CREATED,
    response_model=list[UserView],
    dependencies=[InstanceDepends.InstanceMaintainer],
)
def permissions_users_add(
    instance_permission_service: InstancePermissionAnnotations.InstancePermissionService,  # noqa: E501
    user_service: UserAnnotations.UserService,
    permission: InstancePermission,
    instance: InstanceAnnotations.GetInstance,
    permission_user_in: InstancePermissionUserAddRemove,
):
    user = user_service.get_user_record(
        user_id=permission_user_in.user_id,
        username=permission_user_in.username,
    )
    return instance_permission_service.user_add(
        instance=instance,
        permission=permission,
        user=user,
    )


@router.delete(
    "/{permission}/users",
    summary="Instance Permission User Remove",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[InstanceDepends.InstanceMaintainer],
)
def permissions_users_remove(
    instance_permission_service: InstancePermissionAnnotations.InstancePermissionService,  # noqa: E501
    user_service: UserAnnotations.UserService,
    permission: InstancePermission,
    instance: InstanceAnnotations.GetInstance,
    permission_user_in: InstancePermissionUserAddRemove,
):
    user = user_service.get_user_record(
        user_id=permission_user_in.user_id,
        username=permission_user_in.username,
    )
    return instance_permission_service.user_remove(
        instance=instance,
        permission=permission,
        user=user,
    )


@router.post(
    "/{permission}/groups",
    summary="Instance Permission Group Add",
    status_code=status.HTTP_201_CREATED,
    response_model=list[UserView],
    dependencies=[InstanceDepends.InstanceMaintainer],
)
def permissions_groups_add(
    instance_permission_service: InstancePermissionAnnotations.InstancePermissionService,  # noqa: E501
    permission_group_service: PermissionGroupAnnotations.PermissionGroupService,
    permission: InstancePermission,
    instance: InstanceAnnotations.GetInstance,
    permission_group_in: InstancePermissionGroupAddRemove,
):
    group = permission_group_service.get_permission_group_record(
        group_id=permission_group_in.group_id,
        groupname=permission_group_in.groupname,
    )
    return instance_permission_service.group_add(
        instance=instance,
        permission=permission,
        group=group,
    )


@router.delete(
    "/{permission}/groups",
    summary="Instance Permission Group Remove",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[InstanceDepends.InstanceMaintainer],
)
def permissions_groups_remove(
    instance_permission_service: InstancePermissionAnnotations.InstancePermissionService,  # noqa: E501
    permission_group_service: PermissionGroupAnnotations.PermissionGroupService,
    permission: InstancePermission,
    instance: InstanceAnnotations.GetInstance,
    permission_group_in: InstancePermissionGroupAddRemove,
):
    group = permission_group_service.get_permission_group_record(
        group_id=permission_group_in.group_id,
        groupname=permission_group_in.groupname,
    )
    return instance_permission_service.group_remove(
        instance=instance,
        permission=permission,
        group=group,
    )
