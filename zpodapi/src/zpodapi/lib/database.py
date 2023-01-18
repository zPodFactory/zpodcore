import logging
from collections.abc import Generator
from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from zpodapi import models  # noqa: F401
from zpodapi import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.POSTGRES_DSN,
    echo=settings.ECHO_SQL,
    echo_pool=settings.ECHO_POOL,
)


def create_tables():
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None]:
    with Session(engine) as session:
        yield session


get_session_ctx = contextmanager(get_session)
