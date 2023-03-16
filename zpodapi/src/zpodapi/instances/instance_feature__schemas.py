from typing import Any

from sqlmodel import SQLModel

from zpodapi.lib.schema_base import Req


class InstanceFeatureView(SQLModel):
    id: int = Req(example=1)
    data: dict[Any, Any] = Req(example="{'feature':'one'}")
