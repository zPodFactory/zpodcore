"""Prefect diagnostics helper.

zpodcore has no `flow_run_id` stored on the zpod/component record, but
flow-run names are predictable (`f"Deploy {zpod_name}"`,
`f"Destroy {zpod_name}"`, `f"{component_uid}-download"`, etc.) - so a
name-substring lookup against the Prefect REST API `/flow_runs/filter`
(most recent first) reliably finds the relevant run for diagnostics.
"""

import time

import httpx

TERMINAL_STATE_TYPES = {"COMPLETED", "FAILED", "CRASHED", "CANCELLED"}


class PrefectDiagnostics:
    def __init__(self, api_url: str, ui_url: str):
        self.api_url = api_url.rstrip("/")
        self.ui_url = ui_url.rstrip("/")
        self._client = httpx.Client(timeout=10)

    def find_flow_run(self, name_contains: str) -> dict | None:
        """Return the most recent flow run whose name contains `name_contains`, or None."""
        try:
            resp = self._client.post(
                f"{self.api_url}/flow_runs/filter",
                json={
                    "flow_runs": {"name": {"like_": f"%{name_contains}%"}},
                    "sort": "START_TIME_DESC",
                    "limit": 1,
                },
            )
            resp.raise_for_status()
            runs = resp.json()
            return runs[0] if runs else None
        except httpx.HTTPError:
            return None

    def deploy_timings(self, zpod_name: str) -> dict:
        """The latest `Deploy <zpod_name>` flow run's total run time and each
        component's deploy task time, in seconds: {"flow": 320, "components":
        {"proxmox-9.1.4 (prox11)": 152, ...}}. Empty dict if Prefect can't say."""
        try:
            resp = self._client.post(
                f"{self.api_url}/flow_runs/filter",
                json={"flow_runs": {"name": {"any_": [f"Deploy {zpod_name}"]}},
                      "sort": "START_TIME_DESC", "limit": 1},
            )
            resp.raise_for_status()
            runs = resp.json()
            if not runs:
                return {}
            resp = self._client.post(
                f"{self.api_url}/task_runs/filter",
                json={"flow_runs": {"id": {"any_": [runs[0]["id"]]}}, "limit": 200},
            )
            resp.raise_for_status()
            components = {}
            for task in resp.json():
                name = task["name"]
                if name.endswith(": deploy") and name.startswith(f"{zpod_name} "):
                    components[name[len(zpod_name) + 1 : -len(": deploy")]] = task["total_run_time"]
            return {"flow": runs[0]["total_run_time"], "components": components}
        except httpx.HTTPError:
            return {}

    def wait_for_flow_run(
        self, name_contains: str, *, timeout_seconds: int, interval_seconds: int = 5
    ) -> dict | None:
        """Poll until a flow run matching `name_contains` appears and reaches a
        terminal state, or the timeout elapses.

        Some outcomes (e.g. component upload -> checksum-match sync) have no
        observable status change anywhere except Prefect itself while the
        flow runs - there's nothing else to poll. Returns the last-seen flow
        run dict (possibly still non-terminal, or None if it never appeared).
        """
        start = time.monotonic()
        run = None
        try:
            while time.monotonic() - start < timeout_seconds:
                run = self.find_flow_run(name_contains)
                if run and run.get("state_type") in TERMINAL_STATE_TYPES:
                    self._log_report_card(run)
                    return run
                time.sleep(interval_seconds)
            if run:
                self._log_report_card(run)
            return run
        finally:
            self._log_wait(name_contains, time.monotonic() - start, run)

    def _log_report_card(self, run: dict) -> None:
        try:
            from e2e.report import recorder

            recorder.log_prefect(run, self.ui_link(run["id"]))
        except Exception:
            pass  # reporting must never break a test

    def _log_wait(self, name_contains: str, duration: float, run: dict | None) -> None:
        try:
            from e2e.report import recorder

            last_state = run.get("state_type", "?") if run else "no matching flow run found"
            recorder.log_wait(
                f"waiting for Prefect flow run matching '{name_contains}'",
                duration, last_state=str(last_state),
            )
        except Exception:
            pass  # reporting must never break a test

    def get_logs(self, flow_run_id: str, limit: int = 200) -> list[str]:
        try:
            resp = self._client.post(
                f"{self.api_url}/logs/filter",
                json={
                    "logs": {"flow_run_id": {"any_": [flow_run_id]}},
                    "sort": "TIMESTAMP_ASC",
                    "limit": limit,
                },
            )
            resp.raise_for_status()
            return [entry.get("message", "") for entry in resp.json()]
        except httpx.HTTPError:
            return []

    def ui_link(self, flow_run_id: str) -> str:
        return f"{self.ui_url}/flow-runs/flow-run/{flow_run_id}"

    def hint(self, name_contains: str) -> str:
        """Best-effort one-line diagnostic hint to attach to a test failure message."""
        run = self.find_flow_run(name_contains)
        if not run:
            return f"Prefect UI (no matching flow run found for '{name_contains}'): {self.ui_url}"
        return f"Prefect flow run '{run.get('name')}' [{run.get('state_type')}]: {self.ui_link(run['id'])}"
