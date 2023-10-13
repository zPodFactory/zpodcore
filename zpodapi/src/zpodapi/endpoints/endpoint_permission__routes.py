from fastapi import APIRouter, status

from zpodapi.lib.global_dependencies import GlobalDepends
from zpodapi.users.user__schemas import UserView
from zpodcommon.enums import EndpointPermission

from ..permission_groups.permission_group__dependencies import (
    PermissionGroupAnnotations,
)
from ..users.user__dependencies import UserAnnotations
from .endpoint__dependencies import EndpointAnnotations
from .endpoint_permission__dependencies import EndpointPermissionAnnotations
from .endpoint_permission__schemas import (
    EndpointPermissionGroupAddRemove,
    EndpointPermissionUserAddRemove,
    EndpointPermissionView,
)

router = APIRouter(
    prefix="/endpoints/{id}/permissions",
    tags=["endpoints"],
)


@router.get(
    "",
    summary="Endpoint Permissions Get All",
    response_model=list[EndpointPermissionView],
)
def permissions_get_all(
    *,
    endpoint: EndpointAnnotations.GetEndpoint,
):
    return endpoint.permissions


@router.post(
    "/{permission}/users",
    summary="Endpoint Permissions User Add",
    status_code=status.HTTP_201_CREATED,
    response_model=list[UserView],
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def permissions_users_add(
    endpoint_permission_service: EndpointPermissionAnnotations.EndpointPermissionService,  # noqa: E501
    user_service: UserAnnotations.UserService,
    permission: EndpointPermission,
    endpoint: EndpointAnnotations.GetEndpoint,
    permission_user_in: EndpointPermissionUserAddRemove,
):
    user = user_service.get_user_record(
        user_id=permission_user_in.user_id,
        username=permission_user_in.username,
    )
    return endpoint_permission_service.user_add(
        endpoint=endpoint,
        permission=permission,
        user=user,
    )


@router.delete(
    "/{permission}/users",
    summary="Endpoint Permission User Remove",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def permissions_users_remove(
    endpoint_permission_service: EndpointPermissionAnnotations.EndpointPermissionService,  # noqa: E501
    user_service: UserAnnotations.UserService,
    permission: EndpointPermission,
    endpoint: EndpointAnnotations.GetEndpoint,
    permission_user_in: EndpointPermissionUserAddRemove,
):
    user = user_service.get_user_record(
        user_id=permission_user_in.user_id,
        username=permission_user_in.username,
    )
    return endpoint_permission_service.user_remove(
        endpoint=endpoint,
        permission=permission,
        user=user,
    )


@router.post(
    "/{permission}/groups",
    summary="Endpoint Permissions Group Add",
    status_code=status.HTTP_201_CREATED,
    response_model=list[UserView],
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def permissions_groups_add(
    endpoint_permission_service: EndpointPermissionAnnotations.EndpointPermissionService,  # noqa: E501
    permission_group_service: PermissionGroupAnnotations.PermissionGroupService,
    permission: EndpointPermission,
    endpoint: EndpointAnnotations.GetEndpoint,
    permission_group_in: EndpointPermissionGroupAddRemove,
):
    group = permission_group_service.get_permission_group_record(
        group_id=permission_group_in.group_id,
        groupname=permission_group_in.groupname,
    )
    return endpoint_permission_service.group_add(
        endpoint=endpoint,
        permission=permission,
        group=group,
    )


@router.delete(
    "/{permission}/groups",
    summary="Endpoint Permission Group Remove",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def permissions_groups_remove(
    endpoint_permission_service: EndpointPermissionAnnotations.EndpointPermissionService,  # noqa: E501
    permission_group_service: PermissionGroupAnnotations.PermissionGroupService,
    permission: EndpointPermission,
    endpoint: EndpointAnnotations.GetEndpoint,
    permission_group_in: EndpointPermissionGroupAddRemove,
):
    group = permission_group_service.get_permission_group_record(
        group_id=permission_group_in.group_id,
        groupname=permission_group_in.groupname,
    )
    return endpoint_permission_service.group_remove(
        endpoint=endpoint,
        permission=permission,
        group=group,
    )
