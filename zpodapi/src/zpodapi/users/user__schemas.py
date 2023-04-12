from datetime import datetime

from pydantic import EmailStr

from zpodapi.lib.schema_base import Field, SchemaBase


class D:
    id = {"example": 1}
    username = {"example": "jdoe"}
    email = {"example": "jdoe@example.com"}
    description = {"example": "Sample User"}
    ssh_key = {"example": "<key>"}
    superadmin = {"example": False}
    creation_date = {"example": datetime(2023, 1, 1)}
    last_connection_date = {"example": datetime(2023, 1, 1, 0, 1)}


class UserCreate(SchemaBase):
    username: str = Field(..., D.username)
    email: EmailStr = Field(..., D.email)
    description: str = Field("", D.description)
    ssh_key: str = Field("", D.ssh_key)
    superadmin: bool = Field(False, D.superadmin)


class UserUpdate(SchemaBase):
    description: str | None = Field(None, D.description)
    ssh_key: str | None = Field(None, D.ssh_key)


class UserUpdateAdmin(UserUpdate):
    superadmin: bool | None = Field(None, D.superadmin)


class UserView(SchemaBase):
    id: int = Field(..., D.id)
    username: str = Field(..., D.username)
    email: EmailStr = Field(..., D.email)


class UserViewFull(UserView):
    description: str = Field(..., D.description)
    creation_date: datetime = Field(..., D.creation_date)
    last_connection_date: datetime | None = Field(None, D.last_connection_date)
    superadmin: bool = Field(..., D.superadmin)
