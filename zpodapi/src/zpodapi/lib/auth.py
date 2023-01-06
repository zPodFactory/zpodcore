from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKey, APIKeyHeader
from sqlalchemy import func
from sqlmodel import Session, select

from zpodapi.lib.database import get_session
from zpodapi.models import User

api_key_header = APIKeyHeader(name="access_token", auto_error=False)


def get_current_user(
    session: Session = Depends(get_session),
    api_key: APIKey = Security(api_key_header),
):
    if user := session.exec(select(User).where(User.api_token == api_key)).first():
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )


def get_current_user_and_update(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    # Update last connection
    user.last_connection = func.now()
    session.add(user)
    session.commit()
    return user
