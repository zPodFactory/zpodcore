import logging
from collections.abc import Generator
from contextlib import contextmanager
from ipaddress import IPv4Address, IPv4Network, IPv6Address

from psycopg2.extensions import AsIs, register_adapter
from sqlmodel import Session, create_engine

from zpodcommon import models  # noqa: F401
from zpodengine import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.POSTGRES_DSN.unicode_string(),
    echo=settings.ECHO_SQL,
    echo_pool=settings.ECHO_POOL,
)


def adapt_pydantic_ip_address(ip):
    return AsIs(repr(ip.exploded))


def get_session() -> Generator[Session, None]:
    with Session(engine) as session:
        yield session


def get_session_raw():
    return Session(engine)


get_session_ctx = contextmanager(get_session)
register_adapter(IPv4Address, adapt_pydantic_ip_address)
register_adapter(IPv6Address, adapt_pydantic_ip_address)
register_adapter(IPv4Network, adapt_pydantic_ip_address)
