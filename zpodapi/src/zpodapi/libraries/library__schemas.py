from datetime import datetime

from pydantic import Field as PField
from sqlmodel import SQLModel

from zpodapi.lib.schema_base import Field

example_creation_date = datetime(2023, 1, 1)
example_last_modified_date = datetime(2023, 1, 1, 0, 1)


class LibraryCreate(SQLModel, extra="forbid"):
    name: str = Field(..., example="vmware")
    description: str = Field(..., example="Default zPodFactory library")
    git_url: str = Field(..., example="https://github.com/zpodfactory/zpodlibrary")


class LibraryUpdate(SQLModel, extra="forbid"):
    description: str | None = Field(None, example="Default zPodFactory library")
    enabled: bool | None = Field(None, example=False)


class LibraryView(SQLModel):
    name: str = Field(..., example="vmware")
    description: str = Field(..., example="Default zPodFactory library")
    git_url: str = Field(..., example="https://github.com/zpodfactory/zpodlibrary")
    creation_date: datetime = Field(..., example=example_creation_date)
    last_modified_date: datetime | None = PField(
        None,
        example=example_last_modified_date,
        nullable=True,
    )
    enabled: bool = Field(...)
