from sqlmodel import Field, SQLModel


class Setting(SQLModel, table=True):
    __tablename__ = "settings"

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
    )
    name: str = Field(..., unique=True, index=True, nullable=False)
    description: str = Field(
        default="",
        nullable=False,
    )
    value: str = Field(
        default="",
        nullable=False,
    )
