from typing import Any

from sqlmodel import SQLModel

from zpodapi.components.component__schemas import ComponentView
from zpodapi.lib.schema_base import Req


class InstanceComponentView(SQLModel):
    component: ComponentView
    data: dict[Any, Any]


class InstanceComponentCreate(SQLModel, extra="forbid"):
    component_uid: str = Req(example="vcda-4.4.1")
