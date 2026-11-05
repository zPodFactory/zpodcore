"""Generic + resource-specific polling helpers.

zpodcore deployments are slow (real vCenter clones, real downloads), so
every "did this work" check in the suite goes through here rather than a
bare loop in each test - one place to get the timeout/interval/diagnostics
behavior right.
"""

import time
from collections.abc import Callable
from typing import TypeVar

from zpodsdk.errors import UnexpectedStatus

from e2e import status

T = TypeVar("T")


class PollTimeoutError(Exception):
    """Raised when a poll loop exceeds its timeout without reaching a terminal state."""


class PollFailureError(Exception):
    """Raised when a poll loop reaches a known *failure* terminal state."""


def _log_wait(reason: str, duration: float, ticks: int, last_state: str) -> None:
    try:
        from e2e.report import recorder

        recorder.log_wait(reason, duration, ticks=ticks, last_state=last_state)
    except Exception:
        pass  # reporting must never break a test


def poll_until[T](
    fetch: Callable[[], T],
    *,
    is_success: Callable[[T], bool],
    is_failure: Callable[[T], bool],
    describe: Callable[[T], str],
    timeout_seconds: int,
    interval_seconds: int = 10,
    reason: str = "waiting for a terminal state",
) -> T:
    """Poll `fetch()` until `is_success` or `is_failure` is true, or timeout.

    `reason` is a human-readable label for what's being waited on, recorded
    to the HTML report as a "wait" step between whatever triggered the
    poll and whatever comes after it - regardless of how the loop ends
    (success, failure, or timeout).
    """
    start = time.monotonic()
    ticks = 0
    value = fetch()
    try:
        while True:
            elapsed = time.monotonic() - start

            if is_success(value):
                return value
            if is_failure(value):
                raise PollFailureError(
                    f"Reached failure state after {elapsed:.0f}s: {describe(value)}"
                )
            if elapsed >= timeout_seconds:
                raise PollTimeoutError(
                    f"Timed out after {timeout_seconds}s waiting for a terminal state. "
                    f"Last seen: {describe(value)}"
                )

            time.sleep(interval_seconds)
            ticks += 1
            value = fetch()
    finally:
        _log_wait(reason, time.monotonic() - start, ticks, describe(value))


def poll_zpod_status(client, zpod_ref: str, *, timeout_seconds: int, interval_seconds: int = 10):
    """Poll a zpod until ACTIVE, DEPLOY_FAILED, or DESTROY_FAILED.

    `zpod_ref` is the SDK's `id` path selector, e.g. `f"name={zpod_name}"`.
    """
    return poll_until(
        fetch=lambda: client.zpods_get.sync(id=zpod_ref),
        is_success=lambda z: z.status in status.ZPOD_TERMINAL_SUCCESS,
        is_failure=lambda z: z.status in status.ZPOD_TERMINAL_FAILURE,
        describe=lambda z: f"zpod status={z.status}",
        timeout_seconds=timeout_seconds,
        interval_seconds=interval_seconds,
        reason="waiting for zpod to reach ACTIVE or DEPLOY_FAILED",
    )


_NOT_YET_FOUND = object()


def poll_zpod_component_status(
    client, zpod_ref: str, component_ref: str, *, timeout_seconds: int, interval_seconds: int = 10
):
    """Poll a component-within-a-zpod until ACTIVE, ADD_FAILED, or DELETE_FAILED.

    `zpod_ref`/`component_ref` are the SDK's `id`/`component_id` path
    selectors, e.g. `f"name={zpod_name}"` / `f"hostname={hostname}"`.

    `zcli zpod component add` (and `zpods_components_add`) return as soon as
    the add is *scheduled* - the component record itself is only created
    partway through `flow_zpod_component_add`, so a fetch immediately after
    can legitimately 404 for a few seconds. That's "not there yet", not a
    failure - tolerate it instead of crashing on the first poll.
    """

    def fetch():
        try:
            return client.zpods_components_get.sync(id=zpod_ref, component_id=component_ref)
        except UnexpectedStatus as e:
            if e.status_code == 404:
                return _NOT_YET_FOUND
            raise

    return poll_until(
        fetch=fetch,
        is_success=lambda c: c is not _NOT_YET_FOUND and c.status == status.ZPOD_COMPONENT_ACTIVE,
        is_failure=lambda c: c is not _NOT_YET_FOUND and c.status in status.ZPOD_COMPONENT_TERMINAL_FAILURE,
        describe=lambda c: "zpod component not created yet" if c is _NOT_YET_FOUND else f"zpod component status={c.status}",
        timeout_seconds=timeout_seconds,
        interval_seconds=interval_seconds,
        reason="waiting for zpod component to become ACTIVE",
    )


def poll_library_component_download(
    client, component_ref: str, *, timeout_seconds: int, interval_seconds: int = 10
):
    """Poll a library component's download_status until a terminal state (success or FAILED_*).

    `component_ref` is the SDK's `id` path selector, e.g. `f"uid={uid}"`.

    Unlike the other pollers, a `FAILED_*` state here isn't necessarily a
    test bug - the Broadcom-gated-component test *expects*
    FAILED_AUTHENTICATION. Callers should inspect the returned component's
    `download_status` rather than relying on this raising.
    """
    return poll_until(
        fetch=lambda: client.components_get.sync(id=component_ref),
        is_success=lambda c: c.download_status in status.DOWNLOAD_STATUS_TERMINAL,
        is_failure=lambda c: False,
        describe=lambda c: f"component status={c.status} download_status={c.download_status}",
        timeout_seconds=timeout_seconds,
        interval_seconds=interval_seconds,
        reason="waiting for component download to reach a terminal state",
    )


_GONE = object()


def poll_zpod_deleted(client, zpod_ref: str, *, timeout_seconds: int, interval_seconds: int = 10) -> None:
    """Poll until a zpod is gone (404) or reaches status DELETED.

    Unlike the other pollers, `DESTROY_FAILED` is a real failure state here
    too - a zpod stuck destroying is worth failing loudly on.
    """

    def fetch():
        try:
            return client.zpods_get.sync(id=zpod_ref)
        except UnexpectedStatus as e:
            if e.status_code == 404:
                return _GONE
            raise

    poll_until(
        fetch=fetch,
        is_success=lambda z: z is _GONE or z.status == status.ZpodStatus.DELETED,
        is_failure=lambda z: z is not _GONE and z.status == status.ZpodStatus.DESTROY_FAILED,
        describe=lambda z: "zpod gone (404)" if z is _GONE else f"zpod status={z.status}",
        timeout_seconds=timeout_seconds,
        interval_seconds=interval_seconds,
        reason="waiting for zpod deletion to complete",
    )
