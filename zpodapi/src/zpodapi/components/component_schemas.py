from sqlmodel import SQLModel

from zpodapi.lib.schema_base import Field


class ComponentUpdate(SQLModel, extra="forbid"):
    component_uid: str = Field(nullable=False, example="vcda-4.4.1")


class ComponentView(SQLModel):
    component_uid: str = Field(nullable=False, example="vcda-4.4.1")
    component_name: str = Field(nullable=False, example="vcda")
    component_version: str = Field(nullable=False, example="4.4.1")


class ComponentViewFull(ComponentView):
    library_name: str = Field(default=None, foreign_key="libraries.name")
    filename: str | None = Field(
        nullable=False, example="vmware_nsx/vmware-nsxt-4.0.1.1.json"
    )
    enabled: bool = Field(default=False)
    status: str | None = Field(default=None, nullable=True, example="SCHEDULED")
