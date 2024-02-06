from datetime import datetime

from zpodapi.lib.schema_base import Field, SchemaBase


class D:
    id = {"example": 1}
    name = {"example": "default"}
    description = {"example": "Default zPodFactory library"}
    git_url = {"example": "https://github.com/zpodfactory/zpodlibrary"}
    enabled = {"example": True}
    creation_date = {"example": datetime(2023, 1, 1)}
    last_modified_date = {"example": datetime(2023, 1, 1, 0, 1)}


class LibraryCreate(SchemaBase):
    name: str = Field(..., example="default")
    description: str = Field(..., D.description)
    git_url: str = Field(..., D.git_url)


class LibraryUpdate(SchemaBase):
    description: str | None = Field(None, D.description)
    enabled: bool | None = Field(None, D.enabled)


class LibraryView(SchemaBase):
    id: int = Field(..., D.id)
    name: str = Field(..., D.name)
    description: str = Field(..., D.description)
    git_url: str = Field(..., D.git_url)
    enabled: bool = Field(..., D.enabled)
    creation_date: datetime = Field(..., D.creation_date)
    last_modified_date: datetime | None = Field(None, D.last_modified_date)
