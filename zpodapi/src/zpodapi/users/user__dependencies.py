from fastapi import Depends, HTTPException
from sqlmodel import Session

from zpodapi.lib import dependencies

from .user__services import UserService
from .user__types import UserIdType


def get_user_record(
    *,
    session: Session = Depends(dependencies.get_session),
    id: UserIdType,
):
    if user := UserService(session=session).get(id=id):
        return user
    raise HTTPException(status_code=404, detail="User not found")
