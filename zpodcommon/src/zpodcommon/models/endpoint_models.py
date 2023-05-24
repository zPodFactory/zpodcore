from sqlmodel import JSON, Column, Field

from zpodcommon.models.model_base import ModelBase


class Endpoint(ModelBase, table=True):
    __tablename__ = "endpoints"

    id: int | None = Field(default=None, primary_key=True, nullable=False)
    name: str = Field(..., unique=True, index=True, nullable=False)
    description: str = Field("", nullable=False)
    endpoints: dict = Field(sa_column=Column(JSON))
    enabled: bool = Field(False, nullable=False)
