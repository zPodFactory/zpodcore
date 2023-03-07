import logging
from collections.abc import Generator
from contextlib import contextmanager

from sqlmodel import Session, create_engine

from zpodapi import settings

#
from zpodcommon import models  # noqa: F401

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.POSTGRES_DSN,
    echo=settings.ECHO_SQL,
    echo_pool=settings.ECHO_POOL,
)


def get_session() -> Generator[Session, None]:
    with Session(engine) as session:
        yield session


get_session_ctx = contextmanager(get_session)
