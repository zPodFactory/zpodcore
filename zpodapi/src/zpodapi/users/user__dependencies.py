from typing import Annotated

from fastapi import Depends, HTTPException, Path
from pydantic import EmailStr

from zpodapi.lib.global_dependencies import service_init_annotation
from zpodapi.lib.types import IdValidator
from zpodcommon import models as M

from .user__services import UserService

IdUsernameEmailType = Annotated[
    str,
    IdValidator(
        fields={"id": int, "username": str, "email": EmailStr},
    ),
]


def get_user(
    *,
    user_service: "UserAnnotations.UserService",
    id: Annotated[
        IdUsernameEmailType,
        Path(
            openapi_examples={
                "id": {"value": "1"},
                "username": {"value": "username=jdoe"},
                "email": {"value": "email=jdoe@example.com"},
            },
        ),
    ],
):
    if user := user_service.get(**id):
        return user
    raise HTTPException(status_code=404, detail="User not found")


class UserDepends:
    pass


class UserAnnotations:
    GetUser = Annotated[M.User, Depends(get_user)]
    UserService = service_init_annotation(UserService)
