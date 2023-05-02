from typing import Any

from zpodapi.components.component__schemas import ComponentView
from zpodapi.lib.schema_base import Field, SchemaBase


class D:
    id = {"example": 1}
    component_uid = {"example": "vcda-4.4.1"}
    data = {"example": "{}"}
    extra_id = {"example": "11"}


class InstanceComponentView(SchemaBase):
    component: ComponentView
    data: dict[Any, Any] = Field(..., D.data)


class InstanceComponentCreate(SchemaBase):
    component_uid: str = Field(..., D.component_uid)
    extra_id: str = Field("", D.extra_id)
    data: dict = Field(..., D.data)
