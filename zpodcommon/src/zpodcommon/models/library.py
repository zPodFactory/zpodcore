from datetime import datetime

from sqlmodel import Field, SQLModel


class Library(SQLModel, table=True):
    __tablename__ = "libraries"

    id: int | None = Field(default=None, primary_key=True, nullable=False)
    name: str = Field(..., unique=True, index=True, nullable=False)
    description: str = Field("", nullable=False)
    git_url: str = Field("", nullable=False)
    creation_date: datetime = Field(None, nullable=False)
    lastupdate_date: datetime = Field(None)
    enabled: bool = Field(False, nullable=False)
