from typing import Annotated

from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security.api_key import APIKey, APIKeyHeader
from sqlalchemy import func
from sqlmodel import Session, select

from zpodapi import __version__, settings
from zpodapi.lib.database import get_session  # noqa: F401
from zpodcommon import models as M
from zpodcommon.enums import UserStatus

api_key_header = APIKeyHeader(name="access_token", auto_error=False)


def get_current_user_unvalidated(
    session: "GlobalAnnotations.GetSession",
    api_key: Annotated[APIKey, Security(api_key_header)],
) -> M.User:
    where = [M.User.status == UserStatus.ENABLED]
    if api_key:
        where.append(M.User.api_token == api_key)
    elif settings.DEV_AUTOAUTH_USER:
        where.append(M.User.id == settings.DEV_AUTOAUTH_USER)
    else:
        where.append(M.User.id == -1)
    return session.exec(select(M.User).where(*where)).first()


def get_current_user(
    current_user_unvalidated: "GlobalAnnotations.GetCurrentUserUnvalidated",
) -> M.User:
    if current_user_unvalidated:
        return current_user_unvalidated
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )


def update_last_connection_date(
    session: "GlobalAnnotations.GetSession",
    current_user_unvalidated: "GlobalAnnotations.GetCurrentUserUnvalidated",
) -> None:
    if current_user_unvalidated:
        # Update last connection
        current_user_unvalidated.last_connection_date = func.now()
        session.add(current_user_unvalidated)
        session.commit()


def superadmin(current_user: "GlobalAnnotations.GetCurrentUser") -> bool:
    return current_user.superadmin


def only_superadmin(superadmin: "GlobalAnnotations.SuperAdmin") -> None:
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


def validate_version(
    version: Annotated[str | None, Header(include_in_schema=False)] = None,
):
    # If the version header is included, validate that it matches
    # the current version.  If not, return 417 error.
    if version and version != __version__:
        raise HTTPException(
            status_code=status.HTTP_417_EXPECTATION_FAILED,
            detail={
                "message": "Invalid version",
                "provided_version": version,
                "expected_version": __version__,
            },
        )


class GlobalDepends:
    UpdateLastConnectionDate = Depends(update_last_connection_date)
    OnlySuperAdmin = Depends(only_superadmin)
    ValidateVersion = Depends(validate_version)


class GlobalAnnotations:
    GetSession = Annotated[Session, Depends(get_session)]
    GetCurrentUser = Annotated[M.User, Depends(get_current_user)]
    GetCurrentUserUnvalidated = Annotated[M.User, Depends(get_current_user_unvalidated)]
    SuperAdmin = Annotated[bool, Depends(superadmin)]
