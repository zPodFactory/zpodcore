from typing import Any

from zpodapi.components.component__schemas import ComponentView
from zpodapi.lib.schema_base import Field, SchemaBase


class D:
    id = {"example": 1}
    data = {"example": "{}"}
    component_uid = {"example": "vcda-4.4.1"}


class InstanceComponentView(SchemaBase):
    component: ComponentView
    data: dict[Any, Any] = Field(..., D.data)


class InstanceComponentCreate(SchemaBase):
    component_uid: str = Field(..., D.component_uid)
