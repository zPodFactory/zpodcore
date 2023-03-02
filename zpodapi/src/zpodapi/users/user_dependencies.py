from fastapi import Depends, HTTPException
from sqlmodel import Session

from ..lib import dependencies
from . import user_services
from .user_types import UserIdType


def get_user_record(
    *,
    session: Session = Depends(dependencies.get_session),
    id: UserIdType,
):
    if user := user_services.get(
        session=session,
        id=id,
    ):
        return user
    raise HTTPException(status_code=404, detail="User not found")
