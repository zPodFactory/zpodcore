import builtins
import gzip
import logging
import os
import shutil
import sys
from functools import lru_cache
from logging.handlers import TimedRotatingFileHandler

import anyio
import fastapi
import rich
import starlette
import uvicorn

from zpodapi import settings

logger = logging.getLogger(__name__)
builtins.print = rich.print


def namer(name):
    return f"{name}.gz"


def rotator(source, dest):
    with open(source, "rb") as _f_in, gzip.GzipFile(dest, mode="wb") as _f_out:
        shutil.copyfileobj(_f_in, _f_out)
    os.remove(source)


@lru_cache
def configure_logger():
    handlers = []
    handler_format = logging.Formatter(
        fmt=settings.LOGGER_FORMAT,
        datefmt=settings.LOGGER_FORMAT_DATE,
    )

    if settings.RICH_MODE:
        from rich.logging import RichHandler

        rich_handler = RichHandler(
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            tracebacks_suppress=[anyio, fastapi, starlette, uvicorn],
        )
        rich_handler.setLevel(logging.INFO)
        handlers.append(rich_handler)
    else:
        # Stdout
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(handler_format)
        handlers.append(stdout_handler)

    # File
    if settings.LOGGER_FILENAME:
        output_file_handler = TimedRotatingFileHandler(
            filename=settings.LOGGER_FILENAME,
            when=settings.LOGGER_FILE_WHEN,
            backupCount=settings.LOGGER_FILE_BACKUPCOUNT,
            utc=True,
        )
        output_file_handler.namer = namer
        output_file_handler.rotator = rotator
        output_file_handler.setFormatter(handler_format)
        output_file_handler.setLevel(logging.DEBUG)
        handlers.append(output_file_handler)

    logging.basicConfig(
        level=logging.INFO,
        handlers=handlers,
    )
    logging.getLogger("macbot").setLevel(logging.DEBUG)
