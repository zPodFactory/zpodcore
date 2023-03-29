from typing import Annotated

from fastapi import Depends, HTTPException, Path

from zpodapi.lib.global_dependencies import GlobalAnnotations
from zpodcommon import models as M

from .user__services import UserService
from .user__types import UserIdType


def get_user(
    *,
    session: GlobalAnnotations.GetSession,
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
    if user := UserService(session=session).get(value=id):
        return user
    raise HTTPException(status_code=404, detail="User not found")


class UserDepends:
    GetUser = Depends(get_user)


class UserAnnotations:
    GetUser = Annotated[M.User, UserDepends.GetUser]
