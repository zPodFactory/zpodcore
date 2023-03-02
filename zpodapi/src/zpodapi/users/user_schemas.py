from datetime import datetime

from pydantic import EmailStr
from pydantic import Field as PField
from sqlmodel import SQLModel

from zpodapi.lib.schema_base import Field

example_creation_date = datetime(2023, 1, 1)
example_last_connection = datetime(2023, 1, 1, 0, 1)


class UserCreate(SQLModel, extra="forbid"):
    username: str = Field(..., example="jdoe")
    email: EmailStr = Field(..., example="jdoe@example.com")
    description: str = Field(..., example="Sample User")
    ssh_key: str = Field("")
    superadmin: bool = False


class UserUpdate(SQLModel, extra="forbid"):
    id: int = Field(None, example=1)
    description: str | None = Field(None, example="Sample User")
    ssh_key: str | None = Field(None)
    superadmin: bool | None = Field(None, example=False)


class UserView(SQLModel):
    id: int = Field(..., example=1)
    username: str = Field(..., example="jdoe")
    email: EmailStr = Field(..., example="jdoe@example.com")
    description: str = Field(..., example="Sample User")
    api_token: str = Field(..., index=True)
    ssh_key: str = Field(...)
    creation_date: datetime = Field(..., example=example_creation_date)
    last_connection: datetime | None = PField(
        None,
        example=example_last_connection,
        nullable=True,
    )
    superadmin: bool = Field(...)
