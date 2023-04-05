from typing import Annotated

from fastapi import Depends, HTTPException, Path, status

from zpodapi.lib.global_dependencies import GlobalAnnotations, service_init_annotation
from zpodcommon import models as M

from .user__services import UserService
from .user__types import UserIdType


def get_user(
    *,
    user_service: "UserAnnotations.UserService",
    id: Annotated[
        UserIdType,
        Path(
            examples={
                "id": {"value": "1"},
                "username": {"value": "username=jdoe"},
                "email": {"value": "email=jdoe@example.com"},
            },
        ),
    ],
):
    if user := user_service.get(**UserIdType.args(id)):
        return user
    raise HTTPException(status_code=404, detail="User not found")


def super_admin_or_active_user_only(
    *,
    current_user: GlobalAnnotations.GetCurrentUser,
    user: "UserAnnotations.GetUser",
):
    if not current_user.superadmin and current_user.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges",
        )


class UserDepends:
    SuperAdminOrActiveUserOnly = Depends(super_admin_or_active_user_only)


class UserAnnotations:
    GetUser = Annotated[M.User, Depends(get_user)]
    UserService = service_init_annotation(UserService)
