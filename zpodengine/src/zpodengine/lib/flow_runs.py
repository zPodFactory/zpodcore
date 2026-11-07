"""Stop whatever Prefect is still doing to a zPod before another flow touches it."""

import logging
import time

from prefect import get_run_logger
from prefect.exceptions import MissingContextError
from prefect.runtime import flow_run

from zpodcommon.lib.zpodengine_client import ZpodEngineClient

# A live run reacts to CANCELLING within seconds (the runner SIGTERMs it, then SIGKILLs
# after 30 s). One that is still active after this long has lost its container (host
# reboot, docker restart) and only its Prefect state is left to clean up.
CANCEL_TIMEOUT = 300
POLL_SECONDS = 5


def _logger():
    try:
        return get_run_logger()
    except MissingContextError:
        return logging.getLogger(__name__)


def cancel_zpod_runs(
    zpod_id: int,
    *,
    reason: str,
    client: ZpodEngineClient | None = None,
    timeout: float = CANCEL_TIMEOUT,
    poll: float = POLL_SECONDS,
) -> list[str]:
    """Cancel every other top-level run working on the zPod and wait until none is
    active, runs scheduled meanwhile included. A run that ignores the request for
    ``timeout`` seconds is forced to CANCELLED. Returns the names of the runs cancelled."""
    logger = _logger()
    client = client or ZpodEngineClient()
    own_id = flow_run.id
    asked: dict[str, str] = {}

    def active():
        return [r for r in client.get_zpod_flow_runs(zpod_id) if r["id"] != own_id]

    deadline = time.monotonic() + timeout
    runs = active()
    while runs:
        for run in runs:
            if run["id"] not in asked:
                logger.info(
                    f"Cancelling {run['state']} run {run['name']} ({run['id']})"
                )
                client.cancel_flow_run(run["id"], message=reason)
                asked[run["id"]] = run["name"]
        if time.monotonic() >= deadline:
            break
        time.sleep(poll)
        runs = active()

    for run in runs:
        logger.warning(
            f"Run {run['name']} ({run['id']}) still {run['state']} after {timeout:g} s: "
            "its container is most likely gone, forcing CANCELLED"
        )
        client.cancel_flow_run(run["id"], message=reason, force=True)
    if runs and (runs := active()):
        names = ", ".join(f"{r['name']} ({r['id']})" for r in runs)
        raise RuntimeError(f"Could not cancel runs on zPod {zpod_id}: {names}")
    return list(asked.values())
