from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseSettings, Field, PostgresDsn

_Debug = Literal["debug"]


class Settings(BaseSettings):
    class Config:
        env_prefix = "ZPODAPI_"
        env_file = Path(__file__).parents[1] / ".env"
        frozen = True

    API_USERNAME: str = None
    API_PASSWORD: str = None
    AUTH_ALGORITHM: str = "HS256"
    AUTH_SECRET_KEY: str = "Should_Be_Replaced_1!"
    AUTH_TOKEN_EXPIRE_MINUTES: int = 480

    DEBUGPY: bool = False
    DEV_AUTOAUTH_USER: int | None = None
    DEV_MODE: bool = False
    HOST: str = "TBD"

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

    POSTGRES_DSN: PostgresDsn = Field(
        "postgresql://postgres:password@zpodpostgres/postgres",
        env="ZPODCORE_POSTGRES_DSN",
    )
    POSTGRES_PASSWORD: str = Field("password", env="ZPODCORE_POSTGRES_PASSWORD")


settings = Settings()
