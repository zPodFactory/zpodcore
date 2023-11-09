from fastapi import APIRouter, HTTPException, status

from zpodapi.lib.global_dependencies import GlobalDepends

from ..users.user__schemas import UserView
from .permission_group__dependencies import PermissionGroupAnnotations
from .permission_group__schemas import (
    PermissionGroupCreate,
    PermissionGroupUpdate,
    PermissionGroupUserAdd,
    PermissionGroupView,
)

router = APIRouter(
    prefix="/permission_groups",
    tags=["permission_groups"],
)


@router.get(
    "",
    summary="Get All",
    response_model=list[PermissionGroupView],
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def get_all(
    permission_group_service: PermissionGroupAnnotations.PermissionGroupService,
):
    return permission_group_service.crud.get_all()


@router.get(
    "/{id}",
    summary="Get",
    response_model=PermissionGroupView,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def get(
    permission_group: PermissionGroupAnnotations.GetPermissionGroup,
):
    return permission_group


@router.post(
    "",
    summary="Create",
    status_code=status.HTTP_201_CREATED,
    response_model=PermissionGroupView,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def create(
    permission_group_service: PermissionGroupAnnotations.PermissionGroupService,
    permission_group_in: PermissionGroupCreate,
):
    permission_group_in.name = permission_group_in.name.lower()
    if permission_group_service.crud.get_all_filtered(name=permission_group_in.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflicting record found",
        )

    return permission_group_service.crud.create(
        item_in=permission_group_in,
    )


@router.patch(
    "/{id}",
    summary="Update",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def update(
    permission_group_service: PermissionGroupAnnotations.PermissionGroupService,
    permission_group: PermissionGroupAnnotations.GetPermissionGroup,
    permission_group_in: PermissionGroupUpdate,
):
    permission_group_in.name = permission_group_in.name.lower()
    if permission_group_service.crud.get_all_filtered(name=permission_group_in.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflicting record found",
        )
    return permission_group_service.crud.update(
        item=permission_group,
        item_in=permission_group_in,
    )


@router.delete(
    "/{id}",
    summary="Delete",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def delete(
    permission_group_service: PermissionGroupAnnotations.PermissionGroupService,
    permission_group: PermissionGroupAnnotations.GetPermissionGroup,
):
    return permission_group_service.crud.delete(item=permission_group)


@router.get(
    "/{id}/users",
    summary="Permission Group User Get All",
    response_model=list[UserView],
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def users_get_all(
    permission_group: PermissionGroupAnnotations.GetPermissionGroup,
):
    return permission_group.users


@router.post(
    "/{id}/users",
    summary="Permission Group User Add",
    status_code=status.HTTP_201_CREATED,
    response_model=list[UserView],
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def users_add(
    permission_group_service: PermissionGroupAnnotations.PermissionGroupService,
    permission_group: PermissionGroupAnnotations.GetPermissionGroup,
    permission_user_in: PermissionGroupUserAdd,
):
    return permission_group_service.user_add(
        permission_group=permission_group,
        user_id=permission_user_in.user_id,
    )


@router.delete(
    "/{id}/users/{user_id}",
    summary="Permission Group User Delete",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def users_delete(
    permission_group_service: PermissionGroupAnnotations.PermissionGroupService,
    user_id: int,
    permission_group: PermissionGroupAnnotations.GetPermissionGroup,
):
    return permission_group_service.user_delete(
        permission_group=permission_group,
        user_id=user_id,
    )
