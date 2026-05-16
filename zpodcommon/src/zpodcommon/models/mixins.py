from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class CommonDatesMixin(SQLModel):
    creation_date: datetime = Field(
        sa_column_kwargs={"default": lambda: datetime.now(UTC)},
        nullable=False,
    )
    last_modified_date: datetime = Field(
        sa_column_kwargs={
            "default": lambda: datetime.now(UTC),
            "onupdate": lambda: datetime.now(UTC),
        },
        nullable=False,
    )
