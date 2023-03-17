from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKey, APIKeyHeader
from sqlalchemy import func
from sqlmodel import Session, select

from zpodapi import settings
from zpodapi.lib.database import get_session
from zpodcommon import models as M

api_key_header = APIKeyHeader(name="access_token", auto_error=False)


def get_current_user(
    session: Session = Depends(get_session),
    api_key: APIKey = Security(api_key_header),
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


def get_current_user_and_update(
    session: Session = Depends(get_session),
    user: M.User = Depends(get_current_user),
):
    # Update last connection
    user.last_connection_date = func.now()
    session.add(user)
    session.commit()
    return user
