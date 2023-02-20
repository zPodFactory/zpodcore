from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseSettings, Field, PostgresDsn

_Debug = Literal["debug"]

ENV_PREFIX = "ZPODAPI_"


class Settings(BaseSettings):
    API_USERNAME: str = None
    API_PASSWORD: str = None
    AUTH_ALGORITHM: str = "HS256"
    AUTH_SECRET_KEY: str = "MySt0ng5pas3!"
    AUTH_TOKEN_EXPIRE_MINUTES: int = 480

    DEBUGPY: bool = False
    DEV_MODE: bool = False

    ECHO_POOL: bool | _Debug = False
    ECHO_SQL: bool | _Debug = False

    GUNICORN_ACCESS_LOG: str = "-"
    GUNICORN_BIND: Optional[str] = None
    GUNICORN_ERROR_LOG: str = "-"
    GUNICORN_GRACEFUL_TIMEOUT: int = Field(120, gt=0)
    GUNICORN_KEEP_ALIVE: int = Field(5, gt=0)
    GUNICORN_LOG_LEVEL: str = "info"
    GUNICORN_MAX_WORKERS: Optional[int] = Field(None, gt=0)
    GUNICORN_TIMEOUT: int = Field(120, gt=0)
    GUNICORN_WORKERS: Optional[int] = Field(None, gt=0)
    GUNICORN_WORKERS_PER_CORE: int = Field(1, gt=0)
    GUNICORN_WORKER_TMP_DIR: str = "/dev/shm"

    LOGGER_FILENAME: Path = None
    LOGGER_FILE_BACKUPCOUNT: int = 14
    LOGGER_FILE_LEVEL: str = "DEBUG"
    LOGGER_FILE_WHEN: str = "midnight"
    LOGGER_FORMAT: str = "%(asctime)s %(name)s [%(levelname)s]\t%(message)s"
    LOGGER_FORMAT_DATE: str = "%d-%b-%y %H:%M:%S"

    POSTGRES_DSN: PostgresDsn = "postgresql://postgres:password@zpodpostgres/postgres"
    POSTGRES_PASSWORD: str = "password"

    class Config:
        env_prefix = ENV_PREFIX
        env_file = Path(__file__).parent.parent.joinpath(".env").absolute()
        frozen = True


settings = Settings()
