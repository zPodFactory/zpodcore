from pathlib import Path
from typing import Literal

from pydantic import BaseSettings, Field, PostgresDsn

_Debug = Literal["debug"]


class Settings(BaseSettings):
    class Config:
        env_prefix = "ZPODENGINE_"
        env_file = Path(__file__).parents[3] / ".env"
        frozen = True

    DEV_MODE: bool = False

    ECHO_POOL: bool | _Debug = False
    ECHO_SQL: bool | _Debug = False

    POSTGRES_DSN: PostgresDsn = Field(
        "postgresql://postgres:password@zpodpostgres/postgres",
        env="ZPODCORE_POSTGRES_DSN",
    )
    POSTGRES_PASSWORD: str = Field("password", env="ZPODCORE_POSTGRES_PASSWORD")

    SITE_ID: str = Field("zpod", env="ZPODCORE_SITE_ID")

    VCC_PASSWORD: str = Field("password", env="ZPODCORE_VCC_PASSWORD")
    VCC_USERNAME: str = Field(..., env="ZPODCORE_VCC_USERNAME")


settings = Settings()
