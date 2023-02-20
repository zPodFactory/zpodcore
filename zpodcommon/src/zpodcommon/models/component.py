from sqlmodel import Field, SQLModel


class Component(SQLModel, table=True):
    __tablename__ = "components"

    id: int | None = Field(default=None, primary_key=True, nullable=False)
    library_name: str = Field(default=None, foreign_key="libraries.name")
    filename: str = Field(..., unique=True, index=True, nullable=False)
    enabled: bool = Field(False, nullable=False)
