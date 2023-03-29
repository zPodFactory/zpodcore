from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKey, APIKeyHeader
from sqlalchemy import func
from sqlmodel import Session, select

from zpodapi import settings
from zpodapi.lib.database import get_session  # noqa: F401
from zpodcommon import models as M

api_key_header = APIKeyHeader(name="access_token", auto_error=False)

GetSessionDepends = Depends(get_session)
GetSession = Annotated[Session, Depends(get_session)]


def get_current_user(
    session: GetSession,
    api_key: Annotated[APIKey, Security(api_key_header)],
):
    if settings.DEV_AUTOAUTH_USER:
        criteria = M.User.id == settings.DEV_AUTOAUTH_USER
    else:
        criteria = M.User.api_token == api_key

    if user := session.exec(select(M.User).where(criteria)).first():
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )


GetCurrentUserDepends = Depends(get_current_user)
GetCurrentUser = Annotated[M.User, GetCurrentUserDepends]


def update_last_connection_date(
    session: GetSession,
    user: GetCurrentUser,
):
    # Update last connection
    user.last_connection_date = func.now()
    session.add(user)
    session.commit()
    return user


UpdateLastConnectionDateDepends = Depends(update_last_connection_date)
UpdateLastConnectionDate = Annotated[M.User, UpdateLastConnectionDateDepends]
