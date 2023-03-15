from sqlmodel import Field, SQLModel

from .mixins import CommonDatesMixin


class Component(CommonDatesMixin, SQLModel, table=True):
    __tablename__ = "components"

    id: int | None = Field(default=None, primary_key=True, nullable=False)
    component_uid: str = Field(..., unique=True, nullable=False)
    component_name: str = Field(..., unique=False, nullable=False)
    component_version: str = Field(..., unique=False, nullable=False)
    library_name: str = Field(default=None, foreign_key="libraries.name")
    filename: str = Field(..., unique=True, index=True, nullable=False)
    enabled: bool = Field(False, nullable=False)
    status: str = Field(..., nullable=True)
