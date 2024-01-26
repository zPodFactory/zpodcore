from typing import List

from sqlmodel import JSON, Column, Field

from zpodcommon.models.model_base import ModelBase

from .mixins import CommonDatesMixin


class Profile(CommonDatesMixin, ModelBase, table=True):
    __tablename__ = "profiles"

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
    )
    name: str = Field(
        ...,
        unique=False,
        nullable=False,
    )
    profile: List = Field(
        default=[],
        sa_column=Column(JSON, nullable=False,index=False),
    )
