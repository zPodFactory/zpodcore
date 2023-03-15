from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from .mixins import CommonDatesMixin


class User(CommonDatesMixin, SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True, nullable=False)
    username: str = Field(..., unique=True, index=True, nullable=False)
    email: EmailStr = Field(..., unique=True, index=True, nullable=False)
    description: str = Field("", nullable=False)
    api_token: str = Field("", index=True, nullable=False)
    ssh_key: str = Field("", nullable=False)
    last_connection_date: datetime = Field(None)
    superadmin: bool = Field(False, nullable=False)
