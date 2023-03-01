from fastapi import Depends, HTTPException
from pydantic import EmailStr
from sqlmodel import Session

from ..lib import dependencies
from . import user_services


def get_user_record(
    *,
    session: Session = Depends(dependencies.get_session),
    username: str | None = None,
    email: EmailStr | None = None,
):
    if user := user_services.get(
        session=session,
        username=username,
        email=email,
    ):
        return user
    raise HTTPException(status_code=404, detail="User not found")
