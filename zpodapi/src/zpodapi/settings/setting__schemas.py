from pydantic import AfterValidator, StringConstraints, ValidationInfo
from typing_extensions import Annotated

from zpodapi.lib.schema_base import Field, SchemaBase


def hide_sensitive(v: str, info: ValidationInfo):
    name = info.data["name"]
    if "password" in name or "ssh_key" in name:
        return "********"
    return v


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
    value: Annotated[str, AfterValidator(hide_sensitive)] = Field(..., D.value)
