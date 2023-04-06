from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKey, APIKeyHeader
from sqlalchemy import func
from sqlmodel import Session, select

from zpodapi import settings
from zpodapi.lib.database import get_session  # noqa: F401
from zpodcommon import models as M

api_key_header = APIKeyHeader(name="access_token", auto_error=False)


def get_current_user(
    session: "GlobalAnnotations.GetSession",
    api_key: Annotated[APIKey, Security(api_key_header)],
):
    if api_key:
        criteria = M.User.api_token == api_key
    elif settings.DEV_AUTOAUTH_USER:
        criteria = M.User.id == settings.DEV_AUTOAUTH_USER

    if current_user := session.exec(select(M.User).where(criteria)).first():
        return current_user
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )


def update_last_connection_date(
    session: "GlobalAnnotations.GetSession",
    current_user: "GlobalAnnotations.GetCurrentUser",
):
    # Update last connection
    current_user.last_connection_date = func.now()
    session.add(current_user)
    session.commit()
    return current_user


def superadmin(current_user: "GlobalAnnotations.GetCurrentUser") -> bool:
    return current_user.superadmin


def only_superadmin(superadmin: "GlobalAnnotations.SuperAdmin"):
    if not superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges",
        )


def service_init_annotation(service):
    def inner(
        *,
        session: "GlobalAnnotations.GetSession",
        current_user: "GlobalAnnotations.GetCurrentUser",
    ):
        return service(session=session, current_user=current_user)

    return Annotated[service, Depends(inner)]


class GlobalDepends:
    UpdateLastConnectionDate = Depends(update_last_connection_date)
    OnlySuperAdmin = Depends(only_superadmin)


class GlobalAnnotations:
    GetSession = Annotated[Session, Depends(get_session)]
    GetCurrentUser = Annotated[M.User, Depends(get_current_user)]
    SuperAdmin = Annotated[bool, Depends(superadmin)]
