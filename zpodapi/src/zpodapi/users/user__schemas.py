from datetime import datetime

from pydantic import AfterValidator, EmailStr, StringConstraints, validate_email
from typing_extensions import Annotated

from zpodapi.lib.schema_base import Field, SchemaBase
from zpodcommon.enums import UserStatus


def _lowercase_email(value: str) -> str:
    return validate_email(value)[1].lower()


# pydantic v2 replacement for the old `class EmailStrLower(EmailStr)` with a
# `validate` classmethod — that subclass-with-validate pattern was removed.
EmailStrLower = Annotated[EmailStr, AfterValidator(_lowercase_email)]


class D:
    id = {"example": 1}
    username = {"example": "jdoe"}
    email = {"example": "jdoe@example.com"}
    description = {"example": "Sample User"}
    ssh_key = {"example": "<key>"}
    superadmin = {"example": False}
    creation_date = {"example": datetime(2023, 1, 1)}
    last_connection_date = {"example": datetime(2023, 1, 1, 0, 1)}
    status = {"example": UserStatus.ENABLED}
    api_token = {"example": "BNcsTebGHbIdJjlZ0A2xS0qpSskahVRHO6z61qnRPNw"}


class UserCreate(SchemaBase):
    username: Annotated[str, StringConstraints(to_lower=True)] = Field(..., D.username)
    email: EmailStrLower = Field(..., D.email)
    description: str = Field("", D.description)
    ssh_key: str = Field("", D.ssh_key)
    superadmin: bool = Field(False, D.superadmin)


class UserUpdate(SchemaBase):
    description: str | None = Field(None, D.description)
    ssh_key: str | None = Field(None, D.ssh_key)


class UserUpdateAdmin(UserUpdate):
    superadmin: bool | None = Field(None, D.superadmin)


class UserUpdateStatus(SchemaBase):
    status: str = Field(..., D.status)


class UserUpdateApiToken(SchemaBase):
    api_token: str = Field(..., D.api_token)


class UserView(SchemaBase):
    id: int = Field(..., D.id)
    username: str = Field(..., D.username)
    email: EmailStr = Field(..., D.email)


class UserViewFull(UserView):
    description: str = Field(..., D.description)
    creation_date: datetime = Field(..., D.creation_date)
    # `datetime | None` type annotation is enough — pydantic v2 + OpenAPI 3.1
    # render it as `type: [string, null]`, replacing the old v1 workaround
    # that needed `pydantic.Field(..., nullable=True)`.
    last_connection_date: datetime | None = Field(None, D.last_connection_date)
    superadmin: bool = Field(..., D.superadmin)
    status: str = Field(..., D.status)


class UserViewFullPlus(UserViewFull):
    api_token: str = Field(..., D.api_token)
