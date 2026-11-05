"""Real `zcli` invocation helper.

This is what makes the suite CLI-primary: tests call `zcli_run(...)` to
shell out to the actual `zcli` console script installed in e2e's own venv
(`uv run zcli ...`), rather than only exercising the SDK: operators use
the CLI, so its parsing, output and exit codes are part of what is tested.
"""

import configparser
import glob
import json
import os
import re
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer

E2E_ROOT = Path(__file__).resolve().parents[2]
SVG_DIR = E2E_ROOT / "report_svgs"
# zcli's rich Console has no real terminal to size itself against once piped
# through subprocess.run(capture_output=True) - it falls back to checking
# the COLUMNS env var, and if that's unset too, hardcodes 80. Force a wider
# width so captured --output-svg tables aren't unreadably condensed.
SVG_COLUMNS = "160"
# For calls that render typer/click UI (--help above all) rather than a
# data table - at SVG_COLUMNS width, --help's option/command boxes stretch
# into an oversized decorative panel with no extra information in it. A
# normal terminal-ish width keeps that UI compact and readable instead.
HELP_COLUMNS = "100"


def _slug(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()[:60] or "svg"


_SVG_TEXT_RE = re.compile(r'<text\b[^>]*\bx="([\d.]+)"[^>]*\btextLength="([\d.]+)"[^>]*>(.*?)</text>', re.DOTALL)


def _shift_width(svg_text: str, pattern: str, delta: float, count: int = 0) -> str:
    """Replace the first captured group of every `pattern` match with
    (value - delta), preserving int-vs-float formatting."""

    def repl(m: re.Match) -> str:
        old = m.group(1)
        new_val = float(old) - delta
        new_str = f"{new_val:.1f}" if "." in old else str(int(round(new_val)))
        start, end = m.span(1)
        return m.group(0)[: start - m.start()] + new_str + m.group(0)[end - m.start() :]

    return re.sub(pattern, repl, svg_text, count=count)


def _tighten_terminal_width(svg_text: str) -> str:
    """rich sizes the whole terminal "frame" to the console's configured
    width (forced wide via SVG_COLUMNS so multi-column tables don't wrap) -
    even a short zpod list with two rows gets rendered inside a frame
    that's 160 columns wide, dwarfing the actual table. Measure the real
    rightmost extent of visible text (every line also carries an invisible
    trailing newline character positioned at the far right edge, which
    must be excluded or it would defeat this entirely) and shrink every
    width-bearing attribute in the SVG by the same amount, so the frame
    hugs the content instead of the full forced console width.
    """
    matches = _SVG_TEXT_RE.findall(svg_text)
    if not matches:
        return svg_text

    console_width = max(float(x) for x, _length, _text in matches)
    content_right = max((float(x) + float(length) for x, length, text in matches if text.strip()), default=0.0)
    padding = 24.0
    delta = console_width - (content_right + padding)
    if delta <= 0:
        return svg_text  # content already uses the full forced width - nothing to tighten

    svg_text = _shift_width(svg_text, r'viewBox="0 0 (\d+(?:\.\d+)?) [\d.]+"', delta, count=1)
    # (?<!-) matters: a bare \bwidth= also matches inside stroke-width="1" on
    # this same tag ("-" before "width" still counts as a word boundary) -
    # without it this shrinks the border thickness into a huge negative
    # number instead of the actual frame width.
    svg_text = _shift_width(svg_text, r'<rect fill="#191919"[^>]*?(?<!-)\bwidth="(\d+(?:\.\d+)?)"', delta, count=1)
    svg_text = _shift_width(svg_text, r'-clip-terminal">\s*<rect x="0" y="0" width="(\d+(?:\.\d+)?)"', delta, count=1)
    svg_text = _shift_width(svg_text, r'-line-\d+">\s*<rect x="0" y="[\d.]+" width="(\d+(?:\.\d+)?)"', delta, count=0)
    return svg_text


_SVG_ROOT_RE = re.compile(r'<svg\b[^>]*\bviewBox="0 0 ([\d.]+) ([\d.]+)"[^>]*>(.*)</svg>', re.DOTALL)


def _combine_svgs(svgs: list[str]) -> str:
    """Stack multiple rich-rendered SVGs vertically into one.

    zpodcli's `console_print()` (lib/utils.py) opens a brand new recording
    Console and calls `save_svg(title.lower()+".svg", ...)` every time it's
    called - most commands call it once, but `zpod info`'s multi-panel
    output (Basic Information / Networks / Components) calls it three
    times in a single command, producing three separate files that all
    belong to the same logical screenshot. Combining them here means the
    report shows the whole thing, instead of whichever one file happened
    to survive the diff.
    """
    if len(svgs) == 1:
        return svgs[0]
    parts = []
    max_width = 0.0
    y = 0.0
    gap = 16.0
    for svg in svgs:
        m = _SVG_ROOT_RE.search(svg)
        if not m:
            continue
        width, height, inner = float(m.group(1)), float(m.group(2)), m.group(3)
        max_width = max(max_width, width)
        parts.append(f'<g transform="translate(0, {y:.1f})">{inner}</g>')
        y += height + gap
    if not parts:
        return svgs[0]
    total_height = max(y - gap, 0.0)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {max_width:.1f} {total_height:.1f}">'
        + "".join(parts)
        + "</svg>"
    )


def _capture_new_svg(start_wall_time: float, label: str) -> tuple[str, str] | None:
    """Find every `*.svg` in E2E_ROOT written at or after `start_wall_time`
    and, if one or more appeared, tighten and (if more than one) combine
    them, moving the result into `report_svgs/` under a unique name, and
    return (content, path-relative-to-E2E_ROOT).

    Selects by *mtime*, not "wasn't present in a before-snapshot" - a
    filename-diff approach was fooled by a stale same-named leftover from
    an earlier (buggy, since fixed) capture: zpodcli derives each file's
    name deterministically from its panel title (e.g. "Networks" ->
    networks.svg), so if a file with that exact name already happened to
    exist from something else, overwriting it wouldn't register as "new"
    in a before/after set diff at all. mtime doesn't have that blind spot.

    Also handles multi-file commands: `--output-svg` names each file after
    the rendered table's title, and most commands render exactly one, but
    `zpod info`'s multi-panel output calls zpodcli's console_print() three
    times in one command, producing three separate files that all belong
    to the same logical screenshot (see _combine_svgs). Moving whatever's
    captured out immediately (renamed with a timestamp+uuid suffix) also
    means running the same command twice never overwrites the previous
    capture, and leaves the raw SVGs around for an operator to open
    directly instead of just embedding them in the HTML report.
    """
    new_paths = sorted(
        (p for p in map(Path, glob.glob(str(E2E_ROOT / "*.svg"))) if p.stat().st_mtime >= start_wall_time),
        key=lambda p: p.stat().st_mtime,
    )
    if not new_paths:
        return None
    tightened = [_tighten_terminal_width(p.read_text()) for p in new_paths]
    content = _combine_svgs(tightened)
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    dest = SVG_DIR / f"{time.strftime('%H%M%S')}-{_slug(label)}-{uuid.uuid4().hex[:6]}.svg"
    for p in new_paths:
        p.unlink(missing_ok=True)
    dest.write_text(content)
    return content, str(dest.relative_to(E2E_ROOT))


class CliCommandError(Exception):
    def __init__(self, args: list[str], returncode: int, stdout: str, stderr: str):
        self.args = args
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(
            f"`zcli {' '.join(args)}` exited {returncode}\n"
            f"--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}"
        )


@dataclass
class CliResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str
    json: Any = None
    svg: str | None = None
    svg_path: str | None = None


def zcli_run(
    *args: str,
    factory: str | None = None,
    check: bool = True,
    timeout: int = 120,
    columns: str = SVG_COLUMNS,
) -> CliResult:
    """Run `zcli <args>` as a subprocess, using e2e's own venv.

    Not every zcli subcommand supports `--json` - pass it explicitly in
    `args` for the ones that do (most list/info/create commands) and parse
    `.json` on the result; otherwise fall back to `.stdout`.

    `columns` defaults to SVG_COLUMNS (wide, for table-rendering list/info
    commands), but typer/click's own UI - `--help` above all - also sizes
    itself to COLUMNS, and a 160-wide box of short option descriptions is
    just an oversized decorative panel with no extra information in it.
    Pass a narrower `columns` for calls that aren't rendering a data table.
    """
    cmd = ["uv", "run", "zcli"]
    if factory:
        cmd += ["--factory", factory]
    # Always ask for an SVG "screenshot" - harmless no-op for commands that
    # don't render a table (create/delete/enable/...), a real capture for
    # list/info commands. See _capture_new_svg for the overwrite-avoidance.
    cmd += ["--output-svg"]
    cmd += list(args)

    # Small safety margin before the real start: filesystem mtime
    # granularity (1s on some filesystems) could otherwise round a
    # file written a few ms into the call down to *before* our own
    # wall-clock read of "now", making a real capture look stale.
    svg_start_wall_time = time.time() - 1.0
    start = time.monotonic()
    proc = subprocess.run(
        cmd,
        cwd=E2E_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        env={**os.environ, "COLUMNS": columns},
    )
    call_duration = time.monotonic() - start
    captured = _capture_new_svg(svg_start_wall_time, label=" ".join(args) or "output")
    svg, svg_path = captured if captured else (None, None)

    parsed = None
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            parsed = None

    try:
        from e2e.report import recorder

        recorder.log_cli(list(args), proc.returncode, proc.stdout, call_duration, svg=svg, svg_path=svg_path)
    except Exception:
        pass  # reporting must never break a test

    if check and proc.returncode != 0:
        raise CliCommandError(list(args), proc.returncode, proc.stdout, proc.stderr)

    return CliResult(
        args=list(args),
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        json=parsed,
        svg=svg,
        svg_path=svg_path,
    )


def zcli_run_json(*args: str, factory: str | None = None, timeout: int = 120) -> CliResult:
    """Like `zcli_run`, but appends `--json --no-color` and asserts the
    result parsed as JSON.

    `--no-color` matters: without it, zcli's JSON output goes through
    rich's syntax highlighter, which is not guaranteed to be valid JSON
    once captured from a non-tty pipe. Every JSON-parsing call in the
    suite should go through this helper rather than passing `--json` to
    `zcli_run` directly.
    """
    result = zcli_run(*args, "--json", "--no-color", factory=factory, timeout=timeout)
    assert result.json is not None, (
        f"expected JSON output from `zcli {' '.join(args)}` but got:\n{result.stdout}"
    )
    return result


def add_factory(name: str, server: str, token: str) -> None:
    """Registers a factory without making it active.

    Every `zcli_run` call in this suite passes `--factory <name>`
    explicitly (see `RoleRunner`), which bypasses "active" entirely
    (`FactoryConfig.factory` short-circuits on `GLOBAL_FLAGS["factory"]`
    before ever consulting which entry is marked active) - so e2e never
    needs `--setactive`. This also avoids two real problems: hijacking the
    operator's actual active factory context, and `zcli factory remove`
    refusing to remove whichever factory happens to be active (discovered
    against a live server).

    `~/.config/zcli/.zclirc` is local CLI state, not a server-side
    resource - a session killed mid-run (Ctrl-C, SIGTERM, an interrupted
    background job) skips `_role_identities`' teardown and leaves these
    factory entries behind, which `zcli factory add` then rejects outright
    with "Duplicate factory name found" on the *next* run, failing every
    test that needs a role identity. Removing any stale entry first (a
    no-op if it doesn't exist) makes this idempotent across crashed runs.
    """
    remove_factory(name)
    zcli_run("factory", "add", name, "--server", server, "--token", token)


def _zclirc_path() -> Path:
    return Path(typer.get_app_dir("zcli")) / ".zclirc"


def _other_factory_name(exclude: str) -> str | None:
    """Best-effort read of the local `.zclirc` to find some other registered
    factory - prefers a non-`e2e-` one (the operator's own), so reactivating
    it to unblock a removal restores their real context instead of just
    landing on another throwaway e2e-* entry."""
    path = _zclirc_path()
    if not path.is_file():
        return None
    parser = configparser.ConfigParser()
    try:
        parser.read(path)
    except configparser.Error:
        return None
    candidates = [s for s in parser.sections() if s != exclude]
    non_e2e = [s for s in candidates if not s.startswith("e2e-")]
    return next(iter(non_e2e or candidates), None)


def remove_factory(name: str) -> None:
    """Remove a factory, best-effort - a no-op if it's not registered.

    A crashed previous run (see `add_factory`) can leave a stale e2e
    factory marked *active* in `.zclirc`, which `zcli factory remove`
    refuses to touch ("Cannot remove active factory"). Reactivate some
    other registered factory first so the removal can proceed instead of
    leaving the stale entry stuck forever.
    """
    result = zcli_run("factory", "remove", name, check=False)
    if result.returncode != 0 and "Cannot remove active factory" in result.stdout:
        other = _other_factory_name(exclude=name)
        if other:
            zcli_run("factory", "update", other, "--setactive", check=False)
            zcli_run("factory", "remove", name, check=False)


@dataclass
class RoleRunner:
    """A `zcli` runner bound to one identity's ephemeral factory.

    Call it like a function for a plain run, or use `.run_json(...)` when
    the command supports `--json` and you want the parsed result:

        runner = zcli_as("test_owner")
        runner("zpod", "create", ...)
        settings = runner.run_json("setting", "list").json
    """

    factory: str

    def __call__(self, *args: str, check: bool = True, timeout: int = 120) -> CliResult:
        return zcli_run(*args, factory=self.factory, check=check, timeout=timeout)

    def run_json(self, *args: str, timeout: int = 120) -> CliResult:
        return zcli_run_json(*args, factory=self.factory, timeout=timeout)
