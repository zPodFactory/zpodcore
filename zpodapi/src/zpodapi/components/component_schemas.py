from sqlmodel import SQLModel

from zpodapi.lib.schema_base import Field


class ComponentUpdate(SQLModel, extra="forbid"):
    component_uid: str = Field(..., example="vcda-4.4.1")


class ComponentView(SQLModel):
    component_uid: str = Field(..., example="vcda-4.4.1")
    component_name: str = Field(..., example="vcda")
    component_version: str = Field(..., example="4.4.1")
    library_name: str = Field(default=None, foreign_key="libraries.name")
    filename: str | None = Field(..., example="vmware_nsx/vmware-nsxt-4.0.1.1.json")
    enabled: bool = Field(...)
    status: str | None = Field(..., example="SCHEDULED,DOWNLOAD_COMPLETE")
