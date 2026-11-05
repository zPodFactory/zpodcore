"""Self-contained HTML report generator.

Records what happens during a pytest session (per-test outcome/duration,
plus a chronological *flow* of everything that happened while it ran: every
`zcli` invocation with its own `--output-svg` screenshot, every structured
API expected-vs-actual check, every Prefect flow run looked up, and every
real wait/poll loop) and renders it all into one polished, offline HTML
file at session end - no external assets, so it works by itself as an
email attachment or a file sent straight to an operator who wasn't
watching the run happen.

Each test's flow renders as a single vertical timeline, top (test start)
to bottom (final result): request/response card pairs for CLI calls and
API checks, a slim connector for anything the test had to wait on, and a
card for any Prefect flow run it touched - so an operator can read exactly
what happened and why, not just pass/fail.

Wired in from several places, each guarded so a reporting hiccup can never
fail a real test:
- `e2e.cli.zcli_run` logs every CLI invocation (+ its own SVG screenshot,
  captured per-call and moved into `report_svgs/` so two identical
  commands never overwrite each other and the raw files stay inspectable
  outside the HTML).
- `e2e.polling.poll_until` logs a "wait" step for every real poll loop
  (reason, total duration, tick count).
- `e2e.dns.wait_until_*` logs a structured "dns" step for every real query
  against the resolver (hostname queried, resolver IP, expected vs actual
  result, attempt count) - not just that a poll happened, but what was
  actually asked and answered.
- `e2e.prefect_diag.PrefectDiagnostics.wait_for_flow_run` logs the matched
  flow run and the wait it took to reach a terminal state.
- Tests can call the `api_check(...)` fixture (see conftest.py) to record
  a structured "expected X, got Y" request/response pair for an SDK-direct
  call - used wherever a test's whole point *is* a specific status code,
  not just pass/fail.
- `tests/conftest.py` starts/finishes each test record and renders the
  final HTML at session end.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import threading
import time
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path

from e2e.insight import Insight

_current_test: ContextVar[str | None] = ContextVar("_current_test", default=None)

OUTCOME_COLOR = {
    "passed": "#2ee6a6",
    "failed": "#ff5d7a",
    "skipped": "#ffb454",
    "running": "#6ea8ff",
}
STATE_COLOR = {
    "COMPLETED": "#2ee6a6",
    "FAILED": "#ff5d7a",
    "CRASHED": "#ff5d7a",
    "CANCELLED": "#ffb454",
    "RUNNING": "#6ea8ff",
    "PENDING": "#8b96ab",
    "SCHEDULED": "#8b96ab",
}
KIND_COLOR = {
    "cli": "#6ea8ff",
    "ssh": "#c39bff",
    "api_pass": "#2ee6a6",
    "api_fail": "#ff5d7a",
    "dns_pass": "#2ee6a6",
    "dns_fail": "#ff5d7a",
    "prefect": "#2ee6a6",
    "wait": "#ffb454",
    "note": "#8b96ab",
    "svg": "#2ee6a6",
    "table": "#6ea8ff",
}
KIND_ICON = {
    "cli": "$",
    "ssh": "#",
    "prefect": "⚡",
    "wait": "⏳",
    "note": "✎",
    "svg": "▣",
    "table": "⏱",
}


@dataclass
class TestRecord:
    nodeid: str
    title: str
    description: str
    module: str
    start_offset: float = 0.0
    outcome: str = "running"
    duration: float = 0.0
    detail: str = ""
    flow: list = field(default_factory=list)
    insight: Insight | None = None


class Recorder:
    def __init__(self):
        self._lock = threading.Lock()
        self._session_start: float | None = None
        self._test_clock: dict[str, float] = {}
        self.meta: dict = {}
        self.tests: dict[str, TestRecord] = {}
        self.order: list[str] = []
        self.showcase_svgs: list[tuple[str, str]] = []

    # -- session lifecycle ---------------------------------------------------

    def begin_session(self, meta: dict) -> None:
        with self._lock:
            self._session_start = time.monotonic()
            self.meta = meta

    def _elapsed(self) -> float:
        return time.monotonic() - self._session_start if self._session_start else 0.0

    def _t_rel(self, nodeid: str | None) -> float:
        start = self._test_clock.get(nodeid) if nodeid else None
        return (time.monotonic() - start) if start else 0.0

    # -- per-test lifecycle ---------------------------------------------------

    def start_test(self, nodeid: str, title: str, description: str, module: str, insight: Insight | None = None) -> None:
        with self._lock:
            if nodeid not in self.tests:
                self.tests[nodeid] = TestRecord(
                    nodeid=nodeid, title=title, description=description,
                    module=module, start_offset=self._elapsed(), insight=insight,
                )
                self.order.append(nodeid)
                self._test_clock[nodeid] = time.monotonic()
        _current_test.set(nodeid)

    def finish_test(self, nodeid: str, outcome: str, duration: float, detail: str = "") -> None:
        with self._lock:
            t = self.tests.get(nodeid)
            if t:
                t.outcome = outcome
                t.duration = duration
                t.detail = detail
        _current_test.set(None)

    # -- flow steps, appended in chronological order to whichever test is
    # "current" (ContextVar-based, or an explicit nodeid for logging from a
    # worker thread / outside the fixture-managed banner) ---------------------

    def log_cli(
        self, args: list[str], returncode: int, stdout: str, duration: float,
        svg: str | None = None, svg_path: str | None = None, nodeid: str | None = None,
    ) -> None:
        nodeid = nodeid or _current_test.get()
        with self._lock:
            t = self.tests.get(nodeid)
            if t:
                t.flow.append({
                    "kind": "cli", "t_rel": self._t_rel(nodeid),
                    "cmd": "zcli " + " ".join(a for a in args if a != "--output-svg"),
                    "returncode": returncode, "stdout": stdout[:6000], "duration": duration,
                    "svg": svg, "svg_path": svg_path,
                })

    def log_ssh(
        self, target: str, command: str, returncode: int, output: str, duration: float,
        nodeid: str | None = None,
    ) -> None:
        """Record a command run over SSH on a zPod VM (zcore, a zbox...) - the
        on-host proof behind an API answer."""
        nodeid = nodeid or _current_test.get()
        with self._lock:
            t = self.tests.get(nodeid)
            if t:
                t.flow.append({
                    "kind": "ssh", "t_rel": self._t_rel(nodeid), "target": target,
                    "cmd": command, "returncode": returncode, "stdout": output[:6000],
                    "duration": duration,
                })

    def log_api(
        self, method: str, path: str, description: str, expected: str, actual: str,
        as_expected: bool, note: str = "", nodeid: str | None = None,
    ) -> None:
        """Record a structured request/response pair for an SDK-direct call -
        for tests whose whole point is a specific status code or response
        shape, not just whether the call raised."""
        nodeid = nodeid or _current_test.get()
        with self._lock:
            t = self.tests.get(nodeid)
            if t:
                t.flow.append({
                    "kind": "api", "t_rel": self._t_rel(nodeid),
                    "method": method, "path": path, "description": description,
                    "expected": expected, "actual": actual,
                    "as_expected": as_expected, "note": note,
                })

    def log_dns(
        self, hostname: str, resolver_ip: str, expected: str, actual: str,
        as_expected: bool, duration: float, attempts: int = 0, nodeid: str | None = None,
    ) -> None:
        """Record a real DNS query result - what was asked (hostname, record
        type, which resolver), what the test expected back, and what the
        resolver actually answered. Distinct from `log_wait`: this is the
        query's outcome itself, not just how long something was polled for."""
        nodeid = nodeid or _current_test.get()
        with self._lock:
            t = self.tests.get(nodeid)
            if t:
                t.flow.append({
                    "kind": "dns", "t_rel": self._t_rel(nodeid),
                    "hostname": hostname, "resolver_ip": resolver_ip,
                    "expected": expected, "actual": actual,
                    "as_expected": as_expected, "duration": duration, "attempts": attempts,
                })

    def log_prefect(self, run: dict, ui_link: str, nodeid: str | None = None) -> None:
        nodeid = nodeid or _current_test.get()
        with self._lock:
            t = self.tests.get(nodeid)
            if t:
                t.flow.append({
                    "kind": "prefect", "t_rel": self._t_rel(nodeid),
                    "name": run.get("name", "?"),
                    "state": run.get("state_type", "?"),
                    "id": run.get("id", ""),
                    "ui_link": ui_link,
                })

    def log_wait(
        self, reason: str, duration: float, *, ticks: int = 0, last_state: str = "",
        nodeid: str | None = None,
    ) -> None:
        """Record a real wait/poll loop - what the test was blocked on, for how
        long, and what the last-seen state was."""
        nodeid = nodeid or _current_test.get()
        with self._lock:
            t = self.tests.get(nodeid)
            if t:
                t.flow.append({
                    "kind": "wait", "t_rel": self._t_rel(nodeid),
                    "reason": reason, "duration": duration,
                    "ticks": ticks, "last_state": last_state,
                })

    def log_note(self, text: str, nodeid: str | None = None) -> None:
        nodeid = nodeid or _current_test.get()
        with self._lock:
            t = self.tests.get(nodeid)
            if t:
                t.flow.append({"kind": "note", "t_rel": self._t_rel(nodeid), "text": text})

    def log_table(
        self, title: str, headers: list[str], rows: list[list[str]], *, summary: str = "",
        nodeid: str | None = None,
    ) -> None:
        """A small comparison table in the test's flow (first column left-aligned,
        the rest right-aligned). A row whose first cell starts with "Total" is
        rendered bold."""
        nodeid = nodeid or _current_test.get()
        with self._lock:
            t = self.tests.get(nodeid)
            if t:
                t.flow.append({
                    "kind": "table", "t_rel": self._t_rel(nodeid), "title": title,
                    "headers": headers, "rows": rows, "summary": summary,
                })

    def log_svg(
        self, label: str, svg_markup: str, svg_path: str | None = None, nodeid: str | None = None,
    ) -> None:
        nodeid = nodeid or _current_test.get()
        with self._lock:
            if nodeid and nodeid in self.tests:
                self.tests[nodeid].flow.append({
                    "kind": "svg", "t_rel": self._t_rel(nodeid),
                    "label": label, "svg": svg_markup, "svg_path": svg_path,
                })
            else:
                self.showcase_svgs.append((label, svg_markup))

    # -- rendering -------------------------------------------------------------

    def render_html(self, path: Path) -> Path:
        total_duration = self._elapsed()
        ids = {nodeid: _make_test_id(nodeid) for nodeid in self.order}

        counts = {"passed": 0, "failed": 0, "skipped": 0}
        by_outcome: dict[str, list[tuple[str, str]]] = {"passed": [], "failed": [], "skipped": []}
        by_module: dict[str, list[str]] = {}
        for nodeid in self.order:
            t = self.tests[nodeid]
            counts[t.outcome] = counts.get(t.outcome, 0) + 1
            by_outcome.setdefault(t.outcome, []).append((ids[nodeid], t.title))
            by_module.setdefault(t.module, []).append(nodeid)

        parts = [
            _HEAD,
            _render_header(self.meta, counts, total_duration, by_outcome),
            "<main>",
            _render_index(by_module, self.tests, ids),
            _render_sections(by_module, self.tests, ids),
            _render_showcase(self.showcase_svgs),
            "</main>",
            _render_footer(self.meta),
            _SCRIPT,
            _FOOT,
        ]
        path.write_text("\n".join(parts))
        return path


recorder = Recorder()


def _e(s) -> str:
    return html.escape(str(s), quote=True)


def _fmt_dur(seconds: float) -> str:
    if seconds >= 3600:
        h, rem = divmod(int(seconds), 3600)
        m, s = divmod(rem, 60)
        return f"{h}h {m}m {s}s"
    if seconds >= 60:
        m, s = divmod(int(seconds), 60)
        return f"{m}m {s}s"
    return f"{seconds:.1f}s"


def _make_test_id(nodeid: str) -> str:
    """A stable, URL-fragment-safe anchor id for one test, used to link from
    the header's pass/fail/skip hover cards and the test index straight to
    the (initially collapsed) `<details>` card for that test."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", nodeid).strip("-").lower()
    short_hash = hashlib.sha1(nodeid.encode()).hexdigest()[:6]
    return f"t-{slug[:80]}-{short_hash}"


_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>zpodcore &middot; e2e report</title>
<style>
  :root {
    color-scheme: dark;
    --bg: #060910; --panel: #10151f; --border: #232c3d;
    --text: #e6edf7; --muted: #8b96ab;
    --pass: #2ee6a6; --fail: #ff5d7a; --skip: #ffb454; --info: #6ea8ff;
    --grad1: #6ea8ff; --grad2: #a78bfa; --grad3: #2ee6a6;
  }
  * { box-sizing: border-box; min-width: 0; }
  html { scroll-behavior: smooth; }
  html, body { max-width: 100%; overflow-x: hidden; }
  body {
    background: var(--bg); color: var(--text); margin: 0; padding: 0;
    font-family: -apple-system, "Segoe UI", Inter, Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  a { color: var(--info); }
  svg { max-width: 100%; height: auto; }
  img { max-width: 100%; }

  .reveal { opacity: 0; transform: translateY(14px); transition: opacity .5s ease, transform .5s ease; }
  .reveal.in { opacity: 1; transform: translateY(0); }

  /* ---- sticky nav ---- */
  nav.top {
    position: sticky; top: 0; z-index: 50; display: flex; align-items: center;
    gap: 28px; padding: 14px 40px; background: rgba(6,9,16,.72);
    backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
    border-bottom: 1px solid var(--border);
  }
  nav.top .brand { font-weight: 800; letter-spacing: .02em; font-size: 15px; white-space: nowrap; }
  nav.top .brand span { background: linear-gradient(90deg, var(--grad1), var(--grad2)); -webkit-background-clip: text; background-clip: text; color: transparent; }
  nav.top a { color: var(--muted); text-decoration: none; font-size: 13px; font-weight: 600; white-space: nowrap; }
  nav.top a:hover { color: var(--text); }
  .expand-toggle {
    margin-left: auto; font-size: 12px; font-weight: 700; color: var(--text); white-space: nowrap;
    background: var(--panel); border: 1px solid var(--border); border-radius: 999px; padding: 7px 16px;
    cursor: pointer; font-family: inherit; transition: border-color .15s ease, background .15s ease;
  }
  .expand-toggle:hover { border-color: #4a5468; background: #161c2a; }

  /* ---- hero ---- */
  /* position:relative, no overflow:hidden here - the stat hover popovers
     below are absolutely-positioned descendants of .hero-inner and need
     to be able to overflow past the hero's own bottom edge without being
     clipped. The decorative blur blobs get their own dedicated, fully
     clipped layer instead (.hero-glow) so they don't need the whole
     section to clip. */
  .hero { position: relative; padding: 72px 40px 56px; border-bottom: 1px solid var(--border); }
  .hero-glow { position: absolute; inset: 0; overflow: hidden; z-index: 0; pointer-events: none; }
  .hero-glow::before, .hero-glow::after { content: ""; position: absolute; border-radius: 50%; filter: blur(90px); opacity: .35; }
  .hero-glow::before { width: 480px; height: 480px; background: var(--grad1); top: -220px; left: -120px; }
  .hero-glow::after { width: 420px; height: 420px; background: var(--grad2); bottom: -220px; right: -80px; }
  .hero-inner { position: relative; z-index: 1; max-width: 1300px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; gap: 48px; flex-wrap: wrap; }
  .hero h1 {
    margin: 0; font-size: 44px; font-weight: 800; letter-spacing: -.02em; line-height: 1.1;
    background: linear-gradient(90deg, #fff 10%, var(--grad1) 60%, var(--grad2) 100%);
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }
  .hero .tagline { margin: 10px 0 22px; color: var(--muted); font-size: 15px; max-width: 520px; }
  .pill-row { display: flex; gap: 10px; flex-wrap: wrap; }
  .pill { display: inline-flex; align-items: center; gap: 6px; font-size: 12.5px; color: var(--muted); background: var(--panel); border: 1px solid var(--border); border-radius: 999px; padding: 6px 14px; }
  .pill b { color: var(--text); font-weight: 600; }

  .ring-wrap { position: relative; display: flex; align-items: center; gap: 28px; flex-wrap: wrap; }
  .ring { transform: rotate(-90deg); }
  .ring-bg { fill: none; stroke: var(--border); stroke-width: 12; }
  .ring-fg { fill: none; stroke-width: 12; stroke-linecap: round; stroke-dashoffset: var(--circumference); transition: stroke-dashoffset 1.2s cubic-bezier(.4,0,.2,1) .2s; }
  .ring-fg.in { stroke-dashoffset: var(--offset); }
  .ring-label { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
  .ring-label .pct { font-size: 26px; font-weight: 800; }
  .ring-label .lbl { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; }

  .stat-row { display: flex; gap: 14px; flex-wrap: wrap; }
  .stat-wrap { position: relative; }
  .stat { background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 14px 22px; min-width: 96px; text-align: center; cursor: default; }
  .stat .n { font-size: 24px; font-weight: 800; }
  .stat .l { font-size: 10.5px; color: var(--muted); text-transform: uppercase; letter-spacing: .07em; margin-top: 2px; }
  .stat.pass .n { color: var(--pass); } .stat.fail .n { color: var(--fail); }
  .stat.skip .n { color: var(--skip); } .stat.time .n { color: var(--info); }
  .stat-wrap.has-pop .stat { cursor: pointer; }
  .stat-wrap.has-pop .stat:hover { border-color: #364154; }

  /* ---- stat hover popovers (pass/fail/skip -> which tests) ---- */
  /* top:100% (not +8px) with padding-top standing in for the visual gap,
     not a position offset - a real gap is dead space outside .stat-wrap's
     hoverable box, so moving the mouse straight down from the stat into
     the popover crosses it and instantly loses :hover, making the
     popover disappear before there's any real chance to click a link in
     it. The transparent padding keeps the same look with zero dead zone:
     the popover's own box (hoverable) now starts flush against the stat. */
  .stat-pop {
    display: none; position: absolute; top: 100%; padding-top: 8px; left: 50%; transform: translateX(-50%);
    min-width: 240px; max-width: 340px; z-index: 60; text-align: left;
  }
  .stat-pop-inner {
    max-height: 300px; overflow-y: auto; background: var(--panel); border: 1px solid var(--border);
    border-radius: 12px; padding: 8px; box-shadow: 0 20px 44px -14px rgba(0,0,0,.65);
  }
  .stat-wrap.has-pop:hover .stat-pop { display: block; }
  .stat-pop-head { font-size: 10px; text-transform: uppercase; letter-spacing: .07em; color: var(--muted); padding: 4px 8px 6px; }
  .stat-pop-row { display: block; padding: 7px 8px; border-radius: 7px; font-size: 12.5px; color: var(--text); text-decoration: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .stat-pop-row:hover { background: rgba(255,255,255,.07); }

  main { padding: 8px 40px 100px; max-width: 1300px; margin: 0 auto; }
  section { scroll-margin-top: 70px; }
  h2 { font-size: 24px; font-weight: 800; letter-spacing: -.01em; margin: 64px 0 6px; display: flex; align-items: center; gap: 12px; }
  h2::before { content: ""; width: 5px; height: 24px; border-radius: 3px; background: linear-gradient(180deg, var(--grad1), var(--grad2)); display: inline-block; flex-shrink: 0; }
  .section-sub { color: var(--muted); font-size: 13.5px; margin: 0 0 22px 17px; }

  /* ---- test index (replaces the old timeline - one row per test, links
     down into the matching collapsed test card) ---- */
  .index-list { background: var(--panel); border: 1px solid var(--border); border-radius: 16px; padding: 10px 14px; max-width: 100%; }
  .idx-group-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; margin: 16px 6px 4px; }
  .idx-group:first-child .idx-group-label { margin-top: 6px; }
  .idx-row { display: flex; align-items: center; gap: 12px; padding: 9px 10px; border-radius: 8px; text-decoration: none; color: var(--text); max-width: 100%; }
  .idx-row:hover { background: rgba(255,255,255,.045); }
  .idx-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; box-shadow: 0 0 8px currentColor; }
  .idx-name { flex: 1 1 auto; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .idx-dur { font-family: ui-monospace, monospace; font-size: 11.5px; color: #5b6478; flex-shrink: 0; }
  .idx-outcome { font-size: 10px; text-transform: uppercase; letter-spacing: .05em; font-weight: 800; flex-shrink: 0; width: 62px; text-align: right; }

  /* ---- test cards (collapsible <details>, closed by default) ---- */
  .card {
    position: relative; background: var(--panel); border: 1px solid var(--border); border-radius: 14px;
    padding: 18px 22px; margin: 14px 0; overflow: hidden; max-width: 100%;
    transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
  }
  .card::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--accent, var(--border)); }
  .card:hover { transform: translateY(-2px); border-color: #364154; box-shadow: 0 10px 30px -12px rgba(0,0,0,.6); }
  .card > summary { display: flex; align-items: center; gap: 12px; cursor: pointer; list-style: none; }
  .card > summary::-webkit-details-marker { display: none; }
  .card > summary::marker { content: ""; }
  .chevron { display: inline-block; flex-shrink: 0; width: 12px; font-size: 11px; color: var(--muted); transition: transform .15s ease; }
  .card[open] > summary .chevron { transform: rotate(90deg); }
  .card > summary .title { flex: 1 1 auto; font-weight: 700; font-size: 15.5px; font-family: ui-monospace, SFMono-Regular, monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .card > summary .meta-inline { color: #5b6478; font-size: 11.5px; font-family: ui-monospace, monospace; flex-shrink: 0; }
  .badge { display: inline-flex; align-items: center; gap: 6px; padding: 3px 12px; border-radius: 999px; font-size: 10.5px; font-weight: 800; text-transform: uppercase; letter-spacing: .05em; color: #04150f; flex-shrink: 0; }
  .badge .dot-i { width: 6px; height: 6px; border-radius: 50%; background: #04150f; opacity: .55; }
  .test-body { margin-top: 14px; }
  .test-body .desc { color: var(--text); font-size: 13.5px; margin: 0; white-space: pre-wrap; line-height: 1.6; opacity: .92; }
  pre {
    background: #060910; border: 1px solid var(--border); border-radius: 8px;
    padding: 12px 14px; font-size: 12px; overflow-x: auto; margin: 8px 0 0;
    color: #c9d1d9; white-space: pre-wrap; word-break: break-word; max-width: 100%;
    font-family: ui-monospace, SFMono-Regular, monospace;
  }
  /* ---- JSON syntax colors, for zcli --json response bodies ---- */
  pre.json .jk { color: #79c0ff; }
  pre.json .js { color: #2ee6a6; }
  pre.json .jnum { color: #d29922; }
  pre.json .jb { color: #ff9d7a; font-weight: 600; }
  pre.json .jn { color: #5b6478; font-style: italic; }
  pre.json .jp { color: #6a7385; }

  .svg-frame { background: #060910; border: 1px solid var(--border); border-radius: 8px; padding: 10px; margin: 8px 0 0; overflow-x: auto; max-width: 100%; }
  /* zcli --output-svg screenshots hardcode a 20px terminal font (rich's
     SVG export), much larger than the report's own ~12-13.5px text - scale
     the whole SVG down via width rather than overriding font-size, since
     rich also hardcodes each line's `textLength` to match that font size
     for monospace grid alignment; changing font-size alone without
     textLength would desync and garble the character spacing. */
  .svg-frame svg { max-width: 65%; }
  .note { font-size: 12.5px; color: var(--skip); margin-top: 10px; background: rgba(255,180,84,.08); border: 1px solid rgba(255,180,84,.25); border-radius: 8px; padding: 8px 12px; white-space: pre-wrap; line-height: 1.5; }

  /* ---- vertical flow (request/response cards + wait connectors) ---- */
  .flow { position: relative; margin: 16px 0 0; padding-left: 30px; }
  .flow::before { content: ""; position: absolute; left: 9px; top: 2px; bottom: 2px; width: 2px; background: var(--border); }
  .flow-step { position: relative; margin-bottom: 14px; }
  .flow-step:last-child { margin-bottom: 0; }
  .flow-node {
    position: absolute; left: -30px; top: 0; width: 20px; height: 20px; border-radius: 50%;
    background: var(--bg); border: 2px solid var(--node-color, var(--border)); color: var(--node-color, var(--muted));
    display: flex; align-items: center; justify-content: center; font-size: 10.5px; font-weight: 800; z-index: 1;
  }
  .flow-substack { display: flex; flex-direction: column; max-width: 100%; }
  .flow-card { background: #060910; border: 1px solid var(--border); border-radius: 10px; padding: 10px 14px; max-width: 100%; overflow-x: auto; }
  .flow-substack .flow-card.req { border-bottom-left-radius: 4px; border-bottom-right-radius: 4px; }
  .flow-substack .flow-card.resp { border-top-left-radius: 4px; border-top-right-radius: 4px; }
  .flow-connector { text-align: center; color: #3d4658; font-size: 13px; line-height: 1; margin: -1px 0; }
  .flow-card .fc-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; font-size: 10.5px; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; margin-bottom: 6px; }
  .flow-card b { display: block; color: var(--text); font-weight: 600; font-size: 12.5px; font-family: ui-monospace, monospace; word-break: break-word; }
  .flow-t { font-family: ui-monospace, monospace; color: #5b6478; text-transform: none; letter-spacing: 0; font-size: 10.5px; }
  .fc-desc { color: var(--muted); font-size: 12px; margin-top: 6px; line-height: 1.5; }
  .fc-empty { color: #5b6478; font-size: 12px; font-style: italic; margin-top: 2px; }
  .tbl { border-collapse: collapse; font-size: 12.5px; font-family: ui-monospace, SFMono-Regular, monospace; margin-top: 4px; }
  .tbl th { color: var(--muted); font-weight: 600; font-size: 10.5px; text-transform: uppercase; letter-spacing: .05em; text-align: right; padding: 4px 12px; border-bottom: 1px solid var(--border); }
  .tbl td { text-align: right; padding: 4px 12px; color: var(--text); white-space: nowrap; }
  .tbl th:first-child, .tbl td:first-child { text-align: left; }
  .tbl tr.total td { font-weight: 700; border-top: 1px solid var(--border); }
  .tbl td:last-child { color: var(--pass); }
  .tbl-summary { font-size: 14px; font-weight: 700; color: var(--pass); margin: 2px 0 8px; }
  .fc-saved { font-size: 10.5px; color: #5b6478; margin-top: 8px; font-family: ui-monospace, monospace; }
  .flow-wait-line { font-size: 12px; color: var(--skip); background: rgba(255,180,84,.06); border: 1px dashed rgba(255,180,84,.3); border-radius: 8px; padding: 7px 12px; display: inline-block; max-width: 100%; }
  .cli-exit { font-family: ui-monospace, SFMono-Regular, monospace; font-size: 11px; padding: 1px 8px; border-radius: 999px; background: #0a0e16; border: 1px solid var(--border); }
  .api-method { font-family: ui-monospace, SFMono-Regular, monospace; font-size: 11px; font-weight: 800; padding: 1px 8px; border-radius: 5px; background: rgba(110,168,255,.15); color: var(--info); }
  .api-ev-row { display: flex; gap: 18px; margin-top: 2px; font-size: 12px; flex-wrap: wrap; }
  .api-ev-row .lbl { color: #5b6478; text-transform: uppercase; letter-spacing: .05em; font-size: 10px; display: block; margin-bottom: 2px; }
  .api-ev-row code { font-family: ui-monospace, SFMono-Regular, monospace; }

  /* ---- insight: the human-tester narrative (why/reasoning/expected + cascade) ---- */
  .insight { background: linear-gradient(180deg, rgba(110,168,255,.07), rgba(167,139,250,.03)); border: 1px solid rgba(110,168,255,.25); border-radius: 12px; padding: 14px 18px; margin-top: 14px; }
  .insight-row { display: flex; gap: 14px; margin-bottom: 9px; }
  .insight-row:last-child { margin-bottom: 0; }
  .insight-label { flex: 0 0 78px; font-size: 10px; text-transform: uppercase; letter-spacing: .07em; color: var(--info); font-weight: 800; padding-top: 2px; }
  .insight-text { flex: 1; min-width: 0; font-size: 12.5px; color: var(--text); line-height: 1.6; }

  .cascade { display: flex; align-items: stretch; gap: 0; overflow-x: auto; padding: 22px 4px 6px; margin-top: 4px; }
  .cascade-step { position: relative; background: #0b0f17; border: 1px solid var(--border); border-left: 3px solid var(--step-color, var(--border)); border-radius: 10px; padding: 12px 16px; min-width: 168px; max-width: 220px; flex: 0 0 auto; }
  .cascade-step + .cascade-step { margin-left: 30px; }
  .cascade-arrow { position: absolute; left: -27px; top: 50%; transform: translateY(-50%); color: #4a5468; font-size: 17px; line-height: 1; }
  .cascade-tag { position: absolute; top: -12px; right: 10px; font-size: 8.5px; letter-spacing: .06em; text-transform: uppercase; font-weight: 800; padding: 2px 8px; border-radius: 999px; background: var(--bg); border: 1px solid var(--step-color, var(--border)); color: var(--step-color, var(--muted)); white-space: nowrap; }
  .cascade-pill { display: inline-flex; align-items: center; gap: 5px; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: .04em; color: var(--step-color, var(--muted)); margin-bottom: 7px; font-family: ui-monospace, monospace; }
  .cascade-pill .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--step-color, var(--muted)); box-shadow: 0 0 6px var(--step-color, transparent); flex-shrink: 0; }
  .cascade-label { font-weight: 700; font-size: 13px; font-family: ui-monospace, SFMono-Regular, monospace; word-break: break-word; }
  .cascade-detail { font-size: 11px; color: var(--muted); margin-top: 5px; line-height: 1.5; }

  /* ---- showcase ---- */
  .showcase-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(440px, 1fr)); gap: 20px; }
  .showcase-card { background: var(--panel); border: 1px solid var(--border); border-radius: 16px; padding: 18px; overflow-x: auto; position: relative; transition: transform .15s ease, box-shadow .15s ease; max-width: 100%; }
  .showcase-card::before { content: ""; position: absolute; left: 18px; right: 18px; top: 0; height: 3px; border-radius: 0 0 3px 3px; background: linear-gradient(90deg, var(--grad1), var(--grad3)); }
  .showcase-card:hover { transform: translateY(-3px); box-shadow: 0 14px 34px -14px rgba(0,0,0,.65); }
  .showcase-card h3 { margin: 6px 0 12px; font-size: 13.5px; color: var(--muted); font-weight: 700; text-transform: uppercase; letter-spacing: .05em; }

  footer { text-align: center; color: #5b6478; font-size: 12.5px; padding: 40px 24px 50px; }
  footer .brand2 { color: var(--muted); font-weight: 700; }
</style>
</head>
<body>
"""

_FOOT = "</body></html>"

_SCRIPT = """
<script>
  document.querySelectorAll('.stat .n[data-target]').forEach(function (el) {
    var target = parseFloat(el.getAttribute('data-target'));
    var suffix = el.getAttribute('data-suffix') || '';
    var start = performance.now();
    function tick(now) {
      var p = Math.min(1, (now - start) / 900);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * eased) + suffix;
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });
  var ring = document.querySelector('.ring-fg');
  if (ring) requestAnimationFrame(function () { requestAnimationFrame(function () { ring.classList.add('in'); }); });
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { if (e.isIntersecting) e.target.classList.add('in'); });
  }, { threshold: 0.05 });
  document.querySelectorAll('.reveal').forEach(function (el) { io.observe(el); });
  // Any link into a test's anchor (stat hover cards, the test index) should
  // open that test's collapsed <details> card before the browser scrolls to it.
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a[href^="#t-"]');
    if (!a) return;
    var el = document.getElementById(a.getAttribute('href').slice(1));
    if (el && el.tagName === 'DETAILS') { el.open = true; }
  });
  // Expand all / collapse all - flips every test card at once, for
  // switching into a full detailed read-through instead of clicking
  // through 75 cards one at a time.
  var toggleBtn = document.getElementById('toggle-all');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', function () {
      var expanding = toggleBtn.getAttribute('data-state') === 'collapsed';
      document.querySelectorAll('#sections details.card').forEach(function (el) { el.open = expanding; });
      toggleBtn.setAttribute('data-state', expanding ? 'expanded' : 'collapsed');
      toggleBtn.textContent = expanding ? 'Collapse all' : 'Expand all';
    });
  }
</script>
"""


def _nav() -> str:
    return """
<nav class="top">
  <div class="brand">zpod<span>core</span> &middot; e2e</div>
  <a href="#index">Test index</a>
  <a href="#sections">Test sections</a>
  <a href="#showcase">Live showcase</a>
  <button type="button" id="toggle-all" class="expand-toggle" data-state="collapsed">Expand all</button>
</nav>
"""


def _ring_svg(pct: float) -> str:
    r = 52
    circumference = 2 * 3.14159265 * r
    offset = circumference * (1 - pct / 100)
    color = "var(--pass)" if pct >= 90 else ("var(--skip)" if pct >= 60 else "var(--fail)")
    return f"""
<div style="position:relative;width:128px;height:128px;">
  <svg class="ring" width="128" height="128" viewBox="0 0 128 128">
    <circle class="ring-bg" cx="64" cy="64" r="{r}"></circle>
    <circle class="ring-fg" cx="64" cy="64" r="{r}" stroke="{color}"
      style="--circumference:{circumference:.1f}px;--offset:{offset:.1f}px;"
      stroke-dasharray="{circumference:.1f}" stroke-dashoffset="{circumference:.1f}"></circle>
  </svg>
  <div class="ring-label"><div class="pct">{pct:.0f}%</div><div class="lbl">pass rate</div></div>
</div>
"""


def _render_stat(css_class: str, label: str, count: int, items: list[tuple[str, str]]) -> str:
    pop = ""
    wrap_class = "stat-wrap"
    if items:
        wrap_class += " has-pop"
        rows = "".join(f'<a class="stat-pop-row" href="#{tid}">{_e(title)}</a>' for tid, title in items)
        pop = (
            f'<div class="stat-pop"><div class="stat-pop-inner">'
            f'<div class="stat-pop-head">{_e(label)} ({len(items)})</div>{rows}'
            f'</div></div>'
        )
    return f"""
<div class="{wrap_class}">
  <div class="stat {css_class}"><div class="n" data-target="{count}">0</div><div class="l">{_e(label)}</div></div>
  {pop}
</div>"""


def _render_header(meta: dict, counts: dict, total_duration: float, by_outcome: dict[str, list[tuple[str, str]]]) -> str:
    total = sum(counts.values()) or 1
    # Pass rate is over tests that actually ran (passed + failed) - a
    # skipped test (missing fixture data, feature-flag not configured,
    # etc.) is neither a pass nor a fail, so it shouldn't drag the score
    # down. A run where nothing failed reads as 100%, not "value diluted
    # by skips."
    graded = counts.get("passed", 0) + counts.get("failed", 0)
    pct = 100.0 * counts.get("passed", 0) / graded if graded else 100.0
    minutes = total_duration / 60
    pass_stat = _render_stat("pass", "passed", counts.get("passed", 0), by_outcome.get("passed", []))
    fail_stat = _render_stat("fail", "failed", counts.get("failed", 0), by_outcome.get("failed", []))
    skip_stat = _render_stat("skip", "skipped", counts.get("skipped", 0), by_outcome.get("skipped", []))
    return f"""
{_nav()}
<div class="hero">
  <div class="hero-glow"></div>
  <div class="hero-inner">
    <div>
      <h1>End-to-end report</h1>
      <div class="tagline">Live run against a real zPodFactory stack &mdash; real zcli, real Prefect flows, real infrastructure. {total} checks total.</div>
      <div class="pill-row">
        <span class="pill">target <b>{_e(meta.get('api_base_url', '?'))}</b></span>
        <span class="pill">endpoint <b>{_e(meta.get('endpoint_name', '?'))}</b></span>
        <span class="pill">duration <b>{_e(_fmt_dur(total_duration))}</b></span>
        <span class="pill">generated <b>{_e(meta.get('generated_at', '?'))}</b></span>
      </div>
    </div>
    <div class="ring-wrap">
      {_ring_svg(pct)}
      <div class="stat-row">
        {pass_stat}
        {fail_stat}
        {skip_stat}
        <div class="stat-wrap"><div class="stat time"><div class="n" data-target="{minutes:.0f}" data-suffix="m">0</div><div class="l">wall time</div></div></div>
      </div>
    </div>
  </div>
</div>
"""


def _render_index(by_module: dict[str, list[str]], tests: dict[str, TestRecord], ids: dict[str, str]) -> str:
    if not by_module:
        return ""
    groups = []
    for module in sorted(by_module):
        rows = []
        for nodeid in by_module[module]:
            t = tests[nodeid]
            color = OUTCOME_COLOR.get(t.outcome, "#8b949e")
            rows.append(f"""
  <a class="idx-row" href="#{ids[nodeid]}">
    <span class="idx-dot" style="background:{color};color:{color};"></span>
    <span class="idx-name">{_e(t.title)}</span>
    <span class="idx-dur">{t.duration:.1f}s</span>
    <span class="idx-outcome" style="color:{color};">{_e(t.outcome)}</span>
  </a>""")
        groups.append(f'<div class="idx-group"><div class="idx-group-label">{_e(module)}</div>{"".join(rows)}</div>')

    return f"""
<section id="index">
<h2>Test index</h2>
<div class="section-sub">Every test that ran, grouped by module &mdash; click a row to jump to it below and expand its full detail.</div>
<div class="index-list reveal">
{''.join(groups)}
</div>
</section>
"""


def _render_sections(by_module: dict[str, list[str]], tests: dict[str, TestRecord], ids: dict[str, str]) -> str:
    out = ['<section id="sections"><h2>Test sections</h2><div class="section-sub">Every test that ran, grouped by module and collapsed by default &mdash; click one to expand its full step-by-step flow.</div>']
    for module in sorted(by_module):
        out.append(f'<h3 style="margin-top:36px;font-size:16px;color:var(--muted);">{_e(module)}</h3>')
        for nodeid in by_module[module]:
            t = tests[nodeid]
            color = OUTCOME_COLOR.get(t.outcome, "#8b949e")
            desc = t.description.strip() or "(no docstring - see source for what this checks)"
            out.append(f"""
<details class="card reveal" id="{ids[nodeid]}" style="--accent:{color};">
  <summary>
    <span class="chevron">&#9656;</span>
    <span class="title">{_e(t.title)}</span>
    <span class="meta-inline">{t.duration:.1f}s</span>
    <span class="badge" style="background:{color};"><span class="dot-i"></span>{_e(t.outcome)}</span>
  </summary>
  <div class="test-body">
    <div class="desc">{_e(desc)}</div>
    {f'<div class="note">{_e(t.detail)}</div>' if t.detail else ''}
    {_render_insight(t.insight)}
    {_render_flow(t.flow)}
  </div>
</details>""")
    out.append("</section>")
    return "\n".join(out)


def _render_insight(insight: Insight | None) -> str:
    """The human-tester narrative: why this test exists, the reasoning
    behind its expected outcome, and (optionally) the cause-and-effect
    chain that led to it, rendered as a left-to-right cascade strip - see
    e2e.insight for the data model and when to use one."""
    if insight is None:
        return ""
    rows = []
    if insight.why:
        rows.append(f'<div class="insight-row"><span class="insight-label">why</span><span class="insight-text">{_e(insight.why)}</span></div>')
    if insight.reasoning:
        rows.append(f'<div class="insight-row"><span class="insight-label">reasoning</span><span class="insight-text">{_e(insight.reasoning)}</span></div>')
    if insight.expected:
        rows.append(f'<div class="insight-row"><span class="insight-label">expected</span><span class="insight-text">{_e(insight.expected)}</span></div>')
    cascade = _render_cascade(insight.beats)
    return f'<div class="insight reveal">{"".join(rows)}{cascade}</div>'


def _render_cascade(beats: list) -> str:
    if not beats:
        return ""
    steps = []
    for i, beat in enumerate(beats):
        color = f"var(--{beat.color})" if beat.color in ("pass", "fail", "skip") else "var(--info)"
        arrow = '<div class="cascade-arrow">&#8594;</div>' if i > 0 else ""
        tag = f'<div class="cascade-tag" style="--step-color:{color};">{_e(beat.tag)}</div>' if beat.tag else ""
        state = f'<span class="cascade-pill" style="--step-color:{color};"><span class="dot"></span>{_e(beat.state)}</span>' if beat.state else ""
        steps.append(f"""
<div class="cascade-step" style="--step-color:{color};">
  {arrow}{tag}
  {state}
  <div class="cascade-label">{_e(beat.label)}</div>
  <div class="cascade-detail">{_e(beat.detail)}</div>
</div>""")
    return f'<div class="cascade">{"".join(steps)}</div>'


def _json_token_html(value, indent: int) -> str:
    pad = "  " * indent
    pad_in = "  " * (indent + 1)
    if isinstance(value, dict):
        if not value:
            return '<span class="jp">{}</span>'
        rows = [
            f'{pad_in}<span class="jk">&quot;{_e(k)}&quot;</span><span class="jp">:</span> {_json_token_html(v, indent + 1)}'
            for k, v in value.items()
        ]
        return '<span class="jp">{</span>\n' + ',\n'.join(rows) + f'\n{pad}<span class="jp">}}</span>'
    if isinstance(value, list):
        if not value:
            return '<span class="jp">[]</span>'
        rows = [f'{pad_in}{_json_token_html(v, indent + 1)}' for v in value]
        return '<span class="jp">[</span>\n' + ',\n'.join(rows) + f'\n{pad}<span class="jp">]</span>'
    if isinstance(value, bool):
        return f'<span class="jb">{"true" if value else "false"}</span>'
    if value is None:
        return '<span class="jn">null</span>'
    if isinstance(value, str):
        return f'<span class="js">&quot;{_e(value)}&quot;</span>'
    return f'<span class="jnum">{value}</span>'


def _render_json(raw: str) -> str | None:
    """Syntax-colorize a zcli --json response the same way a browser devtools
    panel would - keys, strings, numbers, booleans, and punctuation each get
    their own color instead of a flat wall of `<pre>` text. Returns None
    (caller falls back to plain <pre>) if `raw` isn't valid JSON - not every
    zcli command supports --json, and this has to work either way."""
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None
    return f'<pre class="json">{_json_token_html(parsed, 0)}</pre>'


_ANSI_RE = re.compile(r"\x1b\[([\d;?]*)([A-Za-z])")
_ANSI_FG = {
    30: "#3d4658", 31: "#ff5d7a", 32: "#2ee6a6", 33: "#ffb454",
    34: "#6ea8ff", 35: "#c297ff", 36: "#56d4dd", 37: "#c9d1d9",
    90: "#5b6478", 91: "#ff8fa3", 92: "#7bf5c9", 93: "#ffd27a",
    94: "#9dc2ff", 95: "#dab6ff", 96: "#8fe6ec", 97: "#f4f7fb",
}


def _apply_sgr_codes(codes: list[int], bold: bool, color: str | None) -> tuple[bool, str | None]:
    for code in codes:
        if code == 0:
            bold, color = False, None
        elif code == 1:
            bold = True
        elif code == 22:
            bold = False
        elif code == 39:
            color = None
        elif code in _ANSI_FG:
            color = _ANSI_FG[code]
    return bold, color


def _ansi_to_html(text: str) -> str:
    """Decode ANSI escape codes in captured `zcli` stdout into real HTML
    spans, instead of leaving raw `\\x1b[35m...\\x1b[0m` sequences as
    visible garbage once html.escape'd verbatim - `zcli` colors/bolds its
    status output (e.g. "deployment success!") even when piped through
    subprocess.run rather than a real tty, so those codes are always
    present in the captured text, not just an edge case.

    Only SGR (color/bold) sequences carry visual meaning once flattened to
    static HTML - cursor movement/line-clear CSI sequences (spinner frame
    control) are dropped silently rather than rendered as spans."""
    out = []
    pos = 0
    bold = False
    color = None
    open_span = False
    for m in _ANSI_RE.finditer(text):
        out.append(_e(text[pos : m.start()]))
        pos = m.end()
        if m.group(2) != "m":
            continue  # cursor/clear-line control code, not a color - nothing to render
        codes = [int(c) for c in m.group(1).split(";") if c] or [0]
        bold, color = _apply_sgr_codes(codes, bold, color)
        if open_span:
            out.append("</span>")
            open_span = False
        if bold or color:
            style = ";".join(s for s in (f"color:{color}" if color else "", "font-weight:700" if bold else "") if s)
            out.append(f'<span style="{style}">')
            open_span = True
    out.append(_e(text[pos:]))
    if open_span:
        out.append("</span>")
    return "".join(out)


def _flow_step_cli(step: dict, t_badge: str) -> str:
    color = KIND_COLOR["cli"]
    rc_color = "var(--pass)" if step["returncode"] == 0 else "var(--fail)"
    if step.get("svg"):
        body = f'<div class="svg-frame">{step["svg"]}</div>'
    else:
        json_html = _render_json(step["stdout"]) if step["stdout"].strip() else None
        if json_html is not None:
            body = json_html
        elif step["stdout"].strip():
            body = f'<pre>{_ansi_to_html(step["stdout"])}</pre>'
        else:
            body = '<div class="fc-empty">(no output)</div>'
    saved = f'<div class="fc-saved">saved to {_e(step["svg_path"])}</div>' if step.get("svg_path") else ""
    return f"""
<div class="flow-step">
  <div class="flow-node" style="--node-color:{color};">{KIND_ICON['cli']}</div>
  <div class="flow-substack">
    <div class="flow-card req">
      <div class="fc-head"><span>zcli command</span>{t_badge}</div>
      <b>$ {_e(step["cmd"])}</b>
    </div>
    <div class="flow-connector">&#8595;</div>
    <div class="flow-card resp">
      <div class="fc-head"><span>response</span><span class="cli-exit" style="color:{rc_color};">exit {step["returncode"]} &middot; {step["duration"]:.1f}s</span></div>
      {body}{saved}
    </div>
  </div>
</div>"""


def _flow_step_ssh(step: dict, t_badge: str) -> str:
    color = KIND_COLOR["ssh"]
    rc_color = "var(--pass)" if step["returncode"] == 0 else "var(--fail)"
    out = step["stdout"].strip()
    body = f'<pre>{_ansi_to_html(step["stdout"])}</pre>' if out else '<div class="fc-empty">(no output)</div>'
    return f"""
<div class="flow-step">
  <div class="flow-node" style="--node-color:{color};">{KIND_ICON['ssh']}</div>
  <div class="flow-substack">
    <div class="flow-card req">
      <div class="fc-head"><span>ssh {_e(step["target"])}</span>{t_badge}</div>
      <b># {_e(step["cmd"])}</b>
    </div>
    <div class="flow-connector">&#8595;</div>
    <div class="flow-card resp">
      <div class="fc-head"><span>on-host output</span><span class="cli-exit" style="color:{rc_color};">exit {step["returncode"]} &middot; {step["duration"]:.1f}s</span></div>
      {body}
    </div>
  </div>
</div>"""


def _flow_step_api(step: dict, t_badge: str) -> str:
    color = KIND_COLOR["api_pass"] if step["as_expected"] else KIND_COLOR["api_fail"]
    mark = "✓" if step["as_expected"] else "✗"
    return f"""
<div class="flow-step">
  <div class="flow-node" style="--node-color:{color};">{mark}</div>
  <div class="flow-substack">
    <div class="flow-card req">
      <div class="fc-head"><span>API request</span>{t_badge}</div>
      <b><span class="api-method">{_e(step["method"])}</span> {_e(step["path"])}</b>
      {f'<div class="fc-desc">{_e(step["description"])}</div>' if step.get("description") else ''}
    </div>
    <div class="flow-connector">&#8595;</div>
    <div class="flow-card resp">
      <div class="fc-head"><span>response</span></div>
      <div class="api-ev-row">
        <div><span class="lbl">expected</span><code>{_e(step["expected"])}</code></div>
        <div><span class="lbl">actual</span><code style="color:{color};">{_e(step["actual"])}</code></div>
      </div>
      {f'<div class="fc-desc">{_e(step["note"])}</div>' if step.get("note") else ''}
    </div>
  </div>
</div>"""


def _flow_step_dns(step: dict, t_badge: str) -> str:
    color = KIND_COLOR["dns_pass"] if step["as_expected"] else KIND_COLOR["dns_fail"]
    mark = "✓" if step["as_expected"] else "✗"
    attempts = f' &middot; {step["attempts"]} attempt(s)' if step.get("attempts") else ""
    return f"""
<div class="flow-step">
  <div class="flow-node" style="--node-color:{color};">{mark}</div>
  <div class="flow-substack">
    <div class="flow-card req">
      <div class="fc-head"><span>DNS query</span>{t_badge}</div>
      <b><span class="api-method">A</span> {_e(step["hostname"])}</b>
      <div class="fc-desc">queried directly against resolver {_e(step["resolver_ip"])} (real UDP query, not the API's own record)</div>
    </div>
    <div class="flow-connector">&#8595;</div>
    <div class="flow-card resp">
      <div class="fc-head"><span>response</span><span class="cli-exit" style="color:{color};">{_fmt_dur(step["duration"])}{attempts}</span></div>
      <div class="api-ev-row">
        <div><span class="lbl">expected</span><code>{_e(step["expected"])}</code></div>
        <div><span class="lbl">actual</span><code style="color:{color};">{_e(step["actual"])}</code></div>
      </div>
    </div>
  </div>
</div>"""


def _flow_step_prefect(step: dict, t_badge: str) -> str:
    color = STATE_COLOR.get(step["state"], "#8b949e")
    return f"""
<div class="flow-step">
  <div class="flow-node" style="--node-color:{color};">{KIND_ICON['prefect']}</div>
  <div class="flow-card" style="margin:0;">
    <div class="fc-head"><span>Prefect flow run</span>{t_badge}</div>
    <b>{_e(step["name"])}</b>
    <div style="margin-top:8px;"><span class="badge" style="background:{color};"><span class="dot-i"></span>{_e(step["state"])}</span>
      <a href="{_e(step["ui_link"])}" target="_blank" style="margin-left:10px;font-size:12px;">open in Prefect &rarr;</a></div>
  </div>
</div>"""


def _flow_step_wait(step: dict, t_badge: str) -> str:
    ticks = f' &middot; {step["ticks"]} poll(s)' if step.get("ticks") else ""
    last = f' &middot; last seen: {_e(step["last_state"])}' if step.get("last_state") else ""
    return f"""
<div class="flow-step">
  <div class="flow-node" style="--node-color:{KIND_COLOR['wait']};">{KIND_ICON['wait']}</div>
  <div class="flow-wait-line">{_e(step["reason"])} &mdash; waited {_fmt_dur(step["duration"])}{ticks}{last}</div>
</div>"""


def _flow_step_note(step: dict, t_badge: str) -> str:
    return f"""
<div class="flow-step">
  <div class="flow-node" style="--node-color:{KIND_COLOR['note']};">{KIND_ICON['note']}</div>
  <div class="note" style="margin:0;">{_e(step["text"])}</div>
</div>"""


def _flow_step_svg(step: dict, t_badge: str) -> str:
    saved = f'<div class="fc-saved">saved to {_e(step["svg_path"])}</div>' if step.get("svg_path") else ""
    return f"""
<div class="flow-step">
  <div class="flow-node" style="--node-color:{KIND_COLOR['svg']};">{KIND_ICON['svg']}</div>
  <div class="flow-card" style="margin:0;">
    <div class="fc-head"><span>{_e(step["label"])}</span>{t_badge}</div>
    <div class="svg-frame">{step["svg"]}</div>{saved}
  </div>
</div>"""


def _flow_step_table(step: dict, t_badge: str) -> str:
    head = "".join(f"<th>{_e(h)}</th>" for h in step["headers"])
    body = "".join(
        f'<tr{" class=total" if str(r[0]).startswith("Total") else ""}>'
        + "".join(f"<td>{_e(c)}</td>" for c in r) + "</tr>"
        for r in step["rows"]
    )
    summary = f'<div class="tbl-summary">{_e(step["summary"])}</div>' if step.get("summary") else ""
    return f"""
<div class="flow-step">
  <div class="flow-node" style="--node-color:{KIND_COLOR['table']};">{KIND_ICON['table']}</div>
  <div class="flow-card" style="margin:0;">
    <div class="fc-head"><span>{_e(step["title"])}</span>{t_badge}</div>{summary}
    <table class="tbl"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>
  </div>
</div>"""


_FLOW_RENDERERS = {
    "cli": _flow_step_cli,
    "ssh": _flow_step_ssh,
    "api": _flow_step_api,
    "dns": _flow_step_dns,
    "prefect": _flow_step_prefect,
    "wait": _flow_step_wait,
    "note": _flow_step_note,
    "svg": _flow_step_svg,
    "table": _flow_step_table,
}


def _render_flow(flow: list[dict]) -> str:
    if not flow:
        return ""
    items = []
    for step in flow:
        renderer = _FLOW_RENDERERS.get(step["kind"])
        if not renderer:
            continue
        t_badge = f'<span class="flow-t">+{step["t_rel"]:.1f}s</span>'
        items.append(renderer(step, t_badge))
    return f'<div class="flow">{"".join(items)}</div>'


def _render_showcase(svgs: list[tuple[str, str]]) -> str:
    if not svgs:
        return ""
    cards = "".join(f'<div class="showcase-card reveal"><h3>{_e(label)}</h3>{svg}</div>' for label, svg in svgs)
    return f"""
<section id="showcase">
<h2>Live state showcase</h2>
<div class="section-sub">Rendered straight from <code>zcli --output-svg</code> against the live server, captured right after the run.</div>
<div class="showcase-grid">{cards}</div>
</section>
"""


def _render_footer(meta: dict) -> str:
    return f"""
<footer>
  <div class="brand2">zpodcore e2e</div>
  generated {_e(meta.get('generated_at', '?'))} against {_e(meta.get('api_base_url', '?'))}
</footer>
"""
