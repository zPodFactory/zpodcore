from sqlmodel import Session, SQLModel, create_engine

from zpodapi import models  # noqa: F401
from zpodapi import settings

engine = create_engine(settings.POSTGRES_DSN)


def create_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


def get_session_one():
    return next(get_session())
