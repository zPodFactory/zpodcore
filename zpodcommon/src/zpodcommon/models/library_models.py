from sqlmodel import Field

from zpodcommon.models.model_base import ModelBase

from .mixins import CommonDatesMixin


class Library(CommonDatesMixin, ModelBase, table=True):
    __tablename__ = "libraries"

    id: int | None = Field(default=None, primary_key=True, nullable=False)
    name: str = Field(..., unique=True, index=True, nullable=False)
    description: str = Field("", nullable=False)
    git_url: str = Field("", nullable=False)
    enabled: bool = Field(True, nullable=False)
