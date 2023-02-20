from datetime import datetime

from sqlmodel import SQLModel

from zpodapi.schemas.base import Field


class ComponentUpdate(SQLModel, extra="forbid"):
    enabled: bool = Field(..., example=True)


class ComponentView(SQLModel):
    library_name: str = Field(default=None, foreign_key="libraries.name")
    filename: str | None = Field(..., example="vmware_nsx/vmware-nsxt-4.0.1.1.json")
    enabled: bool = Field(...)
