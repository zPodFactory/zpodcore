from datetime import datetime

from pydantic import EmailStr
from sqlmodel import SQLModel

from zpodapi.models.base import Field

example_creation_date = datetime(2023, 1, 1)
example_last_connection = datetime(2023, 1, 1, 0, 1)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True, nullable=False)
    username: str = Field(..., unique=True, index=True, nullable=False)
    email: EmailStr = Field(..., unique=True, index=True, nullable=False)
    description: str = Field("", nullable=False)
    api_token: str = Field("", index=True, nullable=False)
    ssh_key: str = Field("", nullable=False)
    creation_date: datetime = Field(None, nullable=False)
    last_connection: datetime = Field(None)
    superadmin: bool = Field(False, nullable=False)


class UserCreate(SQLModel, extra="forbid"):
    username: str = Field(..., example="jdoe")
    email: EmailStr = Field(..., example="jdoe@example.com")
    description: str = Field(..., example="Sample User")
    ssh_key: str = Field("")
    superadmin: bool = False


class UserUpdate(SQLModel, extra="forbid"):
    description: str | None = Field(None, example="Sample User")
    ssh_key: str | None = Field(None)
    superadmin: bool | None = Field(None, example=False)


class UserView(SQLModel):
    username: str = Field(..., example="jdoe")
    email: EmailStr = Field(..., example="jdoe@example.com")
    description: str = Field(..., example="Sample User")
    api_token: str = Field(..., index=True)
    ssh_key: str = Field(...)
    creation_date: datetime = Field(None, example=example_creation_date)
    last_connection: datetime = Field(None, example=example_last_connection)
    superadmin: bool = Field(...)
