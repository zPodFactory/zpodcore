from datetime import datetime

from sqlmodel import Field, SQLModel


class CommonDatesMixin(SQLModel):
    creation_date: datetime = Field(
        sa_column_kwargs=dict(default=datetime.utcnow),
        nullable=False,
    )
    last_modified_date: datetime = Field(
        sa_column_kwargs=dict(
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
        ),
        nullable=False,
    )
