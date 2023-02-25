from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class Component(SQLModel, table=True):
    __tablename__ = "components"

    id: int | None = Field(default=None, primary_key=True, nullable=False)
    library_name: str = Field(default=None, foreign_key="libraries.name")
    filename: str = Field(..., unique=True, index=True, nullable=False)
    enabled: bool = Field(False, nullable=False)


class ComponentBase(BaseModel):
    component_name: str
    component_version: str
    component_state: Optional[bool]


class ComponentInfo(ComponentBase):
    component_status: Optional[str]
    component_type: Optional[str]
    component_description: Optional[str]
    component_url: Optional[str]
    component_engine: Optional[str]
    component_product: Optional[str]
    component_file: Optional[str]
    component_checksum: Optional[str]  #
    component_size: Optional[str]


class ComponentStatus(ComponentBase):
    component_status: str
