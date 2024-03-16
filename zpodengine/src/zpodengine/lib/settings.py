from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

_Debug = Literal["debug"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ZPODENGINE_",
        env_file=Path(__file__).parents[3] / ".env",
        frozen=True,
        extra='ignore'
    )

    DEV_MODE: bool = False

    ECHO_POOL: bool | _Debug = False
    ECHO_SQL: bool | _Debug = False

    POSTGRES_DSN: PostgresDsn = Field(
        "postgresql://postgres:password@zpodpostgres/postgres",
        alias="ZPODCORE_POSTGRES_DSN",
    )
    POSTGRES_PASSWORD: str = Field(
        "password",
        alias="ZPODCORE_POSTGRES_PASSWORD",
    )

    SITE_ID: str = Field(
        "zpod",
        alias="ZPODCORE_SITE_ID",
    )


settings = Settings()
