import logging
import multiprocessing

from zpodapi import settings
from zpodapi.lib.cfglog import configure_logger

configure_logger()
logger = logging.getLogger(__name__)

if settings.DEBUGPY:
    logger.info("Start Debugger")
    import debugpy

    debugpy.listen(("0.0.0.0", 5678))

# Gunicorn config variables
bind = settings.GUNICORN_BIND or "0.0.0.0:8000"

workers = settings.GUNICORN_WORKERS
if not workers:
    workers = max(
        settings.GUNICORN_WORKERS_PER_CORE * multiprocessing.cpu_count(),
        2,
    )
    if settings.GUNICORN_MAX_WORKERS:
        workers = min(workers, settings.GUNICORN_MAX_WORKERS)

loglevel = settings.GUNICORN_LOG_LEVEL
errorlog = settings.GUNICORN_ERROR_LOG
worker_tmp_dir = settings.GUNICORN_WORKER_TMP_DIR
accesslog = settings.GUNICORN_ACCESS_LOG
graceful_timeout = settings.GUNICORN_GRACEFUL_TIMEOUT
timeout = settings.GUNICORN_TIMEOUT
keepalive = settings.GUNICORN_KEEP_ALIVE


# For debugging and testing
logger.info(
    dict(
        loglevel=loglevel,
        workers=workers,
        bind=bind,
        graceful_timeout=graceful_timeout,
        timeout=timeout,
        keepalive=keepalive,
        errorlog=errorlog,
        accesslog=accesslog,
        # Additional, non-gunicorn variables
        workers_per_core=settings.GUNICORN_WORKERS_PER_CORE,
        max_workers=settings.GUNICORN_MAX_WORKERS,
        env_workers=settings.GUNICORN_WORKERS,
        cores=multiprocessing.cpu_count(),
    )
)
