#!/usr/bin/env python

import logging
import os
import subprocess
from pathlib import Path

import uvicorn

from zpodapi import settings
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
    if settings.DEBUGPY:
        logger.info("Start Debugger")
        import debugpy

        debugpy.listen(("0.0.0.0", 5678))

    uvicorn.run(
        "zpodapi.main:api",
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        use_colors=True,
        log_config=None,
        reload=True,
        reload_dirs=["../../.."],
    )
