from sqlmodel import Field

from zpodcommon.models.model_base import ModelBase

from .mixins import CommonDatesMixin


class Component(CommonDatesMixin, ModelBase, table=True):
    __tablename__ = "components"

    id: int | None = Field(default=None, primary_key=True, nullable=False)
    component_uid: str = Field(..., unique=True, nullable=False)
    component_name: str = Field(..., unique=False, nullable=False)
    component_version: str = Field(..., unique=False, nullable=False)
    component_description: str = Field(..., unique=False, nullable=False)
    library_name: str = Field(default=None, foreign_key="libraries.name", nullable=True)
    filename: str = Field(..., unique=False, nullable=False)
    jsonfile: str = Field(..., unique=True, index=True, nullable=False)
    status: str = Field(..., nullable=True)
    download_status: str = Field(..., nullable=True)
