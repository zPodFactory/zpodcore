from typing import Annotated

from fastapi import Depends, HTTPException, Path

from zpodapi.lib import dependencies
from zpodcommon import models as M

from .user__services import UserService
from .user__types import UserIdType


def get_user(
    *,
    session: dependencies.GetSession,
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


GetUserDepends = Depends(get_user)
GetUser = Annotated[M.User, GetUserDepends]
