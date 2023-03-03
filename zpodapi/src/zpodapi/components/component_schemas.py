from sqlmodel import SQLModel

from ..lib.schema_base import Field


class ComponentUpdate(SQLModel, extra="forbid"):
    enabled: bool = Field(..., example=True)


class ComponentView(SQLModel):
    library_name: str = Field(default=None, foreign_key="libraries.name")
    filename: str | None = Field(..., example="vmware_nsx/vmware-nsxt-4.0.1.1.json")
    enabled: bool = Field(...)
    # status: str | None = Field(..., example="SCHEDULED,DOWNLOAD_COMPLETE")
    # component_uid: str = Field(..., example="vcsa-4.4.1")
