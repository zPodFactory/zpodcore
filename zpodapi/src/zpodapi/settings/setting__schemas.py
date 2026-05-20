from typing import Annotated

from pydantic import AfterValidator, StringConstraints, ValidationInfo

from zpodapi.lib.schema_base import Field, SchemaBase

# Setting names whose value must not be returned by the API. The DB still
# holds the real value (read by zpodengine via DBUtils.get_setting_value) —
# the masking is only on SettingView serialisation, so clients can see the
# setting exists but never its content.
SENSITIVE_SETTINGS = frozenset({
    "zpodfactory_broadcom_download_token",
})


def hide_sensitive(v: str, info: ValidationInfo) -> str:
    """Mask the value of known-sensitive settings in API responses.

    An empty value is returned unchanged so admins can see the setting has
    not been configured yet; any non-empty value is replaced with ``********``.
    """
    if info.data.get("name") in SENSITIVE_SETTINGS and v:
        return "********"
    return v


class D:
    id = {"example": 1}
    name = {"example": "zpodfactory_default_domain"}
    description = {"example": "default domain for every zpod (zpodfactory.io)"}
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
