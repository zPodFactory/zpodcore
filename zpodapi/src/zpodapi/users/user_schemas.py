from datetime import datetime

from pydantic import EmailStr
from pydantic import Field as PField
from sqlmodel import SQLModel

from zpodapi.lib.schema_base import Field

example_creation_date = datetime(2023, 1, 1)
example_last_connection_date = datetime(2023, 1, 1, 0, 1)


class UserCreate(SQLModel, extra="forbid"):
    username: str = Field(..., example="jdoe")
    email: EmailStr = Field(..., example="jdoe@example.com")
    description: str = Field(..., example="Sample User")
    ssh_key: str = Field("")
    superadmin: bool = False


class UserUpdate(SQLModel):
    class Config:
        extra = "forbid"
        schema_extra = dict(
            example=dict(
                description="Sample User",
                ssh_key="xxx",
                superadmin=False,
            )
        )

    id: int = Field(None)
    description: str | None = Field(None)
    ssh_key: str | None = Field(None)
    superadmin: bool | None = Field(None)


class UserView(SQLModel):
    id: int = Field(..., example=1)
    username: str = Field(..., example="jdoe")
    email: EmailStr = Field(..., example="jdoe@example.com")


class UserViewFull(UserView):
    description: str = Field(..., example="Sample User")
    api_token: str = Field(..., index=True)
    ssh_key: str = Field(...)
    creation_date: datetime = Field(..., example=example_creation_date)
    last_connection_date: datetime | None = PField(
        None,
        example=example_last_connection_date,
        nullable=True,
    )
    superadmin: bool = Field(...)
