from typing import Annotated

from fastapi import Depends, HTTPException, Path

from zpodapi.lib import dependencies
from zpodcommon import models as M

from .user__services import UserService
from .user__types import UserIdType


def get_user_record(
    *,
    session: dependencies.GetSession,
    id: UserIdType = Path(
        examples={
            "id": {"value": "1"},
            "id alternative": {"value": "id=1"},
            "username": {"value": "username=jdoe"},
            "email": {"value": "email=jdoe@example.com"},
        },
    ),
):
    if user := UserService(session=session).get(value=id):
        return user
    raise HTTPException(status_code=404, detail="User not found")


GetUserRecordDepends = Depends(get_user_record)
GetUserRecord = Annotated[M.User, GetUserRecordDepends]
