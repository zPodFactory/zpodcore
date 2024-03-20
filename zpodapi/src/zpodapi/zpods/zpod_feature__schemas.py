from typing import Any

from zpodapi.lib.schema_base import Field, SchemaBase


class D:
    id = {"example": 1}
    data = {"example": "{'feature':'one'}"}


class ZpodFeatureView(SchemaBase):
    id: int = Field(..., D.id)
    data: dict[str, Any] = Field(..., D.data)
