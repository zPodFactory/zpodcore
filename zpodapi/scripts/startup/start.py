#!/usr/bin/env python

import logging
import os
import subprocess
from pathlib import Path

from zpodapi.lib.cfglog import configure_logger

configure_logger()
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    startup_scripts_path = Path(__file__).parent.absolute()
    os.chdir(startup_scripts_path)
    logger.debug("Checking for prestart.sh script")
    if Path("prestart.sh").is_file():
        logger.debug("Running prestart.sh script")
        subprocess.run(["sh", "prestart.sh"])

subprocess.run(
    [
        "gunicorn",
        "-k",
        "uvicorn.workers.UvicornWorker",
        "-c",
        "/zpodcore/scripts/startup/gunicorn_conf.py",
        "zpodapi.main:api",
    ]
)
