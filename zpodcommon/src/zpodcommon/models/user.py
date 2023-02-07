from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


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
