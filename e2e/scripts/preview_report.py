#!/usr/bin/env python3
"""Dev-only tool: render a full report.html preview populated with every
real test's actual name/docstring, without running a live suite.

Not a PEP723 standalone script like preflight.py/cleanup.py - it imports
the real `tests/` package directly, so it needs `uv run` from inside
`e2e/` (pythonpath=["src"] plus the tests dir on sys.path).

Fake durations/outcomes/CLI output/SVGs are for layout review only; real
runs populate all of this from what actually happened (see conftest.py,
cli.py, polling.py, dns.py, prefect_diag.py).
"""

import ast
import html
import importlib
import random
import sys
from pathlib import Path

E2E_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(E2E_ROOT / "src"))
sys.path.insert(0, str(E2E_ROOT / "tests"))

from e2e.report import Recorder  # noqa: E402

random.seed(7)

MODULE_ICONS_ORDER = [
    "test_factory", "test_settings", "test_libraries_components", "test_profiles",
    "test_zpods", "test_zpods_dns", "test_zpods_concurrency",
    "test_users_groups_permissions", "test_endpoints",
]

# What a test in each module is "about", for building plausible fake zcli
# invocations and fake API paths - not meant to be exact, just representative.
MODULE_TOPIC = {
    "test_factory": "factory",
    "test_settings": "setting",
    "test_libraries_components": "component",
    "test_profiles": "profile",
    "test_zpods": "zpod",
    "test_zpods_dns": "zpod dns",
    "test_zpods_concurrency": "zpod",
    "test_users_groups_permissions": "user",
    "test_endpoints": "endpoint",
}
MODULE_RESOURCE = {
    "test_factory": "root",
    "test_settings": "ff_endpoint_ova_staging",
    "test_libraries_components": "zcore-13.7",
    "test_profiles": "e2e-profile-zcore",
    "test_zpods": "e2e-zcore-01",
    "test_zpods_dns": "e2e-zpod-dns",
    "test_zpods_concurrency": "e2e-zcore-02",
    "test_users_groups_permissions": "e2e-test-owner",
    "test_endpoints": "qa-env",
}
ACTION_VERBS = [
    "create", "delete", "destroy", "add", "remove", "update", "enable",
    "disable", "upload", "resync", "reset", "grant", "revoke", "deploy",
]
STATUS_CODES = [401, 403, 404, 400, 409, 422]


def _fake_svg(title: str, lines: list[str]) -> str:
    # font-size 20 (not a smaller "readable" size) deliberately matches what
    # zcli --output-svg actually produces (rich hardcodes 20px/18px terminal
    # fonts) - so this preview shows the same oversized-relative-to-the-
    # report text the real fix (.svg-frame svg { max-width: 65% }) has to
    # shrink, instead of a fake size that never needed shrinking.
    width = 900
    height = 56 + 28 * len(lines)
    rows = "".join(
        f'<text x="16" y="{56 + 28 * i}" fill="#c9d1d9">{html.escape(line)}</text>'
        for i, line in enumerate(lines)
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'font-family="ui-monospace,monospace" font-size="20">'
        f'<rect width="{width}" height="{height}" fill="#0d1117" rx="6"/>'
        f'<text x="16" y="32" fill="#79c0ff" font-size="18">{html.escape(title)}</text>'
        f"{rows}</svg>"
    )


def _pick_action(name: str) -> str | None:
    for verb in ACTION_VERBS:
        if verb in name:
            return verb
    return None


def _load_insights(module: str) -> dict:
    """Import the real test module (safe - fixtures only run when pytest
    collects/executes, not on a plain import) and pull its real INSIGHTS
    dict, if it defines one. Real narrative data beats faking it."""
    try:
        return getattr(importlib.import_module(module), "INSIGHTS", {})
    except Exception:
        return {}


def discover_tests():
    """Statically parse every tests/test_*.py for module-level `def test_*`
    functions and their docstrings - no live server or fixtures needed."""
    tests = []
    for module in MODULE_ICONS_ORDER:
        path = E2E_ROOT / "tests" / f"{module}.py"
        if not path.is_file():
            continue
        insights = _load_insights(module)
        tree = ast.parse(path.read_text())
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                doc = ast.get_docstring(node) or ""
                tests.append((module, node.name, doc, insights.get(node.name)))
    return tests


def build_flow(r: Recorder, nodeid: str, module: str, name: str, doc: str, outcome: str) -> None:
    """Populate a plausible, varied chronological flow for one test: an
    initial listing call (with a fake terminal SVG screenshot), an action
    call if the test name implies one, a request/response API check if the
    docstring calls out a status code, a wait + Prefect card if the test
    deploys/destroys/downloads anything, and a final verification call -
    top (test start) to bottom (final result), same shape a real run
    produces."""
    topic = MODULE_TOPIC.get(module, "zpod")
    resource = MODULE_RESOURCE.get(module, "e2e-resource")
    action = _pick_action(name)
    topic_words = topic.split()
    fail = outcome == "failed"

    list_svg = _fake_svg(
        f"{topic.title()} List",
        [f"{resource:<28} {'DEPLOY_FAILED' if fail and 'zpod' in topic else 'ACTIVE'}", "..."],
    )
    r.log_cli(
        [*topic_words, "list", "--json", "--no-color"], 0,
        f'[{{"name": "{resource}", "status": "ACTIVE"}}]',
        round(random.uniform(0.3, 0.9), 1), svg=list_svg, svg_path=f"report_svgs/preview-{name}-list.svg",
        nodeid=nodeid,
    )

    if action:
        ok = not fail or random.random() > 0.5
        stdout = (
            f"{resource}: {action} succeeded" if ok
            else f"Error: {action} failed - {resource} is not in a valid state"
        )
        r.log_cli(
            [*topic_words, action, resource], 0 if ok else 1, stdout,
            round(random.uniform(0.4, 2.6), 1), nodeid=nodeid,
        )

    for code in STATUS_CODES:
        if str(code) in doc:
            actual = code if not fail else 200
            r.log_api(
                "DELETE" if "delete" in doc.lower() else "GET",
                f"/{topic_words[0]}s/{{id}}" + ("/dns" if "dns" in topic else ""),
                doc.strip().splitlines()[0],
                code, actual, as_expected=(actual == code),
                note="see the full docstring above for why this status code is correct",
                nodeid=nodeid,
            )
            break

    deploy_like = action in ("create", "destroy", "deploy") or any(
        k in doc.lower() for k in ("deploy", "destroy", "download", "resync", "resolve")
    )
    if deploy_like:
        wait_reason = (
            "waiting for zpod to reach ACTIVE or DEPLOY_FAILED" if "zpod" in topic
            else f"waiting for {topic} operation to complete"
        )
        duration = random.choice([8, 22, 60, 240, 900, 2100])
        r.log_wait(
            wait_reason, duration, ticks=max(1, duration // 15),
            last_state="DEPLOY_FAILED" if fail else "ACTIVE", nodeid=nodeid,
        )
        flow_name = f"Deploy {resource}" if action != "destroy" else f"Destroy {resource}"
        r.log_prefect(
            {"name": flow_name, "state_type": "FAILED" if fail else "COMPLETED", "id": f"fake-{abs(hash(nodeid)) % 999999}"},
            f"http://10.60.76.10:8060/flow-runs/flow-run/fake-{abs(hash(nodeid)) % 999999}",
            nodeid=nodeid,
        )

    final_svg = _fake_svg(
        f"{topic.title()} Info: {resource}",
        [f"name       {resource}", f"status     {'DEPLOY_FAILED' if fail else 'ACTIVE'}"],
    )
    r.log_cli(
        [*topic_words, "info" if action else "list", resource, "--json", "--no-color"], 0,
        f'{{"name": "{resource}", "status": "{"DEPLOY_FAILED" if fail else "ACTIVE"}"}}',
        round(random.uniform(0.2, 0.6), 1), svg=final_svg, svg_path=f"report_svgs/preview-{name}-final.svg",
        nodeid=nodeid,
    )

    if random.random() < 0.15:
        r.log_note(
            "Operator note: this behavior was confirmed empirically against the live "
            "stack, not just from reading the source.",
            nodeid=nodeid,
        )


def main() -> None:
    r = Recorder()
    r.begin_session({
        "api_base_url": "http://10.60.76.10:8000",
        "endpoint_name": "qa-env",
        "generated_at": "2026-07-02 09:40:00 (preview - fake timings/outcomes/SVGs)",
    })

    tests = discover_tests()
    t = 0.0
    for module, name, doc, insight in tests:
        nodeid = f"tests/{module}.py::{name}"
        roll = random.random()
        outcome = "failed" if roll < 0.06 else ("skipped" if roll < 0.12 else "passed")
        duration = round(random.choice([0.3, 0.6, 1.8, 4.2, 21.4, 72.0, 121.6, 340.0]), 1)

        r.start_test(nodeid, name, doc, module, insight=insight)
        r.tests[nodeid].start_offset = t
        t += duration * random.choice([0.15, 0.4, 1.0])  # some overlap to hint at concurrency

        if outcome != "skipped":
            build_flow(r, nodeid, module, name, doc, outcome)

        if outcome == "failed":
            r.finish_test(nodeid, outcome, duration, "(preview) assertion failed")
        else:
            r.finish_test(nodeid, outcome, duration, "")

    r.log_svg("zPod List", _fake_svg("zPod List", [
        "e2e-smoke      e2e-smoke.qa.local     e2e-profile-zcore  ACTIVE",
        "e2e-zcore-01   e2e-zcore-01.qa.local  e2e-profile-zcore  ACTIVE",
    ]))
    r.log_svg("Setting List", _fake_svg("Setting List", [
        "ff_endpoint_ova_staging                true",
        "zpodfactory_broadcom_download_token     ********",
    ]))

    # No real time passes in this script (no actual deploys/waits), so
    # Recorder._elapsed() would read ~0s at render time - back-date the
    # session start by the simulated cumulative duration so the header's
    # "duration" pill and wall-time stat demonstrate real formatting
    # instead of "0.0s".
    r._session_start -= t

    out = E2E_ROOT / "scripts" / "report_preview.html"
    r.render_html(out)
    print(f"wrote {out} ({out.stat().st_size} bytes, {len(tests)} real tests included)")


if __name__ == "__main__":
    main()
