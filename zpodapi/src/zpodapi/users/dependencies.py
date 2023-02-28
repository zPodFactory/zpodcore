from fastapi import Depends, HTTPException
from pydantic import EmailStr
from sqlmodel import Session

from zpodapi.lib import deps

from . import services


def get_user_record(
    *,
    session: Session = Depends(deps.get_session),
    username: str | None = None,
    email: EmailStr | None = None,
):
    if user := services.get(session=session, username=username, email=email):
        return user
    raise HTTPException(status_code=404, detail="User not found")
