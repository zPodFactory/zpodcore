from datetime import datetime
from typing import Optional

from pydantic import EmailStr
from pydantic import Field as PField
from pydantic import constr, validate_email

from zpodapi.lib.schema_base import Field, SchemaBase
from zpodcommon.enums import UserStatus


class EmailStrLower(EmailStr):
    @classmethod
    def validate(cls, value: EmailStr) -> EmailStr:
        email = validate_email(value)[1]
        return email.lower()


class D:
    id = {"example": 1}
    username = {"example": "jdoe"}
    email = {"example": "jdoe@example.com"}
    description = {"example": "Sample User"}
    ssh_key = {"example": "<key>"}
    superadmin = {"example": False}
    creation_date = {"example": datetime(2023, 1, 1)}
    last_connection_date = {"example": datetime(2023, 1, 1, 0, 1)}
    status = {"example": UserStatus.ACTIVE}
    api_token = {"example": "BNcsTebGHbIdJjlZ0A2xS0qpSskahVRHO6z61qnRPNw"}


class UserCreate(SchemaBase):
    username: constr(to_lower=True) = Field(..., D.username)
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

    # Had to use a Pydantic Field instead, because of
    # https://github.com/openapi-generators/openapi-python-client/issues/698 and because
    # sqlmodel intercepts the "nullable" argument
    last_connection_date: Optional[datetime] = PField(
        None,
        **D.last_connection_date,
        nullable=True,
    )
    superadmin: bool = Field(..., D.superadmin)
    status: str = Field(..., D.status)


class UserViewFullPlus(UserViewFull):
    api_token: str = Field(..., D.api_token)
