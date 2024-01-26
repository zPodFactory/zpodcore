from pydantic import StringConstraints
from typing_extensions import Annotated

from zpodapi.lib.schema_base import Field, SchemaBase


class D:
    id = {"example": 1}
    name = {"example": "domain"}
    description = {"example": "default domain for every instances (zpodfactory.io)"}
    value = {"example": "zpodfactory.io"}


class SettingCreate(SchemaBase):
    name: Annotated[str, StringConstraints(to_lower=True)] = Field(
        ..., example="default"
    )
    description: str = Field(..., D.description)
    value: str = Field(..., D.value)


class SettingUpdate(SchemaBase):
    description: str | None = Field(None, D.description)
    value: str | None = Field(None, D.value)


class SettingView(SchemaBase):
    id: int = Field(..., D.id)
    name: str = Field(..., D.name)
    description: str = Field(..., D.description)
    value: str = Field(..., D.value)
