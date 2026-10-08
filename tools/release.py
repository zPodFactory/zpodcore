#!/usr/bin/env python3
"""Cut a version, or check that the repository is fit to cut one. Standard library only.

    python3 tools/release.py --check              # what CI runs on every push
    python3 tools/release.py --draft              # the commits since the last tag, as entry
                                                  # candidates for [Unreleased]; prints, writes nothing
    python3 tools/release.py --draft --write      # ... and writes them under [Unreleased] for you to edit
    python3 tools/release.py 0.3.0 --push --from-commits   # the whole release in one command: fill
                                                  # [Unreleased] from the commits, cut, push
    python3 tools/release.py 0.3.0 --dry-run      # show what a cut would do
    python3 tools/release.py 0.3.0                # cut it: CHANGELOG.md, the version, commit, tag
    python3 tools/release.py 0.3.0 --push         # ... and push main and the tag; the release
                                                  # workflow then publishes the changelog section

A cut, in order, stopping at the first thing that is wrong:

1. The working tree is clean and on `main`; the version has the shape this project uses and
   is above the newest tag; every file the version names exists (packer: the var file).
2. `CHANGELOG.md` has a non-empty `[Unreleased]` section: a release with nothing to say is
   not a release.
3. Nothing that must stay local is tracked (no `.env`, no `*.log`, nothing under `runs/`), and
   no string from the local, git-ignored `.release-denylist` is in the tree or in the commits
   since the last tag. Absent denylist: the check is skipped, loudly.
4. `[Unreleased]` becomes `[X.Y.Z] — <today>` with a fresh empty `[Unreleased]` above it; the
   version moves in VERSION_FILE (and in ALSO_UPDATE); TEST_COMMAND runs, if set.
5. One commit, `Release X.Y.Z`, and an annotated tag `vX.Y.Z`. `--push` pushes both.

`--check` runs step 3 plus the two rules CI enforces on every push: the shipped version equals
the newest changelog section, and every tag has a changelog section.

`--draft` is the starting point for the entries, not the entries: it lists the commits since the
newest tag, oldest first, sorted into Added / Changed / Fixed / Removed by their subject, with
housekeeping commits (docs, page revisions, release tooling) set apart. The person, or the
session, cutting the release rewrites the candidates into what changed for the user of the
tool and why, then runs the cut. `--write` puts the candidates under `[Unreleased]` as they are,
for editing; `--from-commits` on a cut does the same and cuts in the same run, which is the
one-command release for a stretch of plain fixes: the commit subjects become the entries.

The block below is the only part that differs between repositories.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

# ── per-repository configuration ─────────────────────────────────────────────────────
PROJECT = "zpodcore"
# A monorepo: one version for the API, the engine, zcli and zpodsdk. The API defines the
# release, so its __version__ is the source; ALSO_UPDATE moves the other eight markers and
# the SDK requirement the published zpodcli wheel carries.
VERSION_FILE = "zpodapi/src/zpodapi/__init__.py"   # where the shipped version is written
VERSION_PATTERN = r'^__version__ = "(\d+\.\d+\.\d+)"'   # one capture group: the version
VERSION_SHAPE = r"\d+\.\d+\.\d+"                    # what a version looks like here
VERSION_IN_FILE = "{version}"                 # what is written into VERSION_FILE
REQUIRED_FILES: tuple[str, ...] = ()             # must exist before a cut; {version} {major_minor}
ALSO_UPDATE: dict[str, str] = {                  # other files: path -> regex with one group
    "zpodcli/src/zpodcli/__init__.py": r'^__version__ = "([^"]+)"',
    "zpodengine/src/zpodengine/__init__.py": r'^__version__ = "([^"]+)"',
    "zpodsdk/src/zpodsdk/__init__.py": r'^__version__ = "([^"]+)"',
    "zpodapi/pyproject.toml": r'^version = "([^"]+)"',
    "zpodcli/pyproject.toml": r'^version = "([^"]+)"',
    "zpodengine/pyproject.toml": r'^version = "([^"]+)"',
    "zpodsdk/pyproject.toml": r'^version = "([^"]+)"',
    "zpodsdk_builder/pyproject.toml": r'^version = "([^"]+)"',
    # The SDK requirement in the zpodcli wheel: `~=X.Y.Z` lets a zpodcli-only patch ship
    # without an SDK upload. Same file, second pattern; dict keys must differ, hence "./".
    "./zpodcli/pyproject.toml": r'^    "zpodsdk~=([^"]+)",',
}
# Refreshes both lockfiles, runs the four suites, builds the two wheels and checks the
# zpodcli wheel requires the SDK released beside it. Runs before the commit; `git add -A`
# then puts the refreshed locks into the Release commit the tag points at.
TEST_COMMAND: tuple[str, ...] = ("tools/release_pretest.sh",)   # () when there is no suite
MUST_STAY_LOCAL = r"(^|/)\.env$|\.log$|(^|/)runs/|(^|/)docs/|^uv\.lock$|^misc/(?!zcore-transition\.sh$|zdnsmasqservers)"
# ─────────────────────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"
DENYLIST = ROOT / ".release-denylist"


def git(*args: str, check: bool = True) -> str:
    return subprocess.run(("git", *args), cwd=ROOT, capture_output=True, text=True, check=check).stdout.strip()


def fail(message: str) -> None:
    print(f"✗ {message}", file=sys.stderr)
    raise SystemExit(1)


def ok(message: str) -> None:
    print(f"✓ {message}")


def vkey(version: str) -> tuple[int, ...]:
    return tuple(int(p) for p in re.findall(r"\d+", version))


def major_minor(version: str) -> str:
    return ".".join(version.split(".")[:2])


# ── the changelog and the version ────────────────────────────────────────────────────


def changelog_versions() -> list[str]:
    """Versions with a section, newest first, `[Unreleased]` excluded."""
    return [m.group(1) for m in re.finditer(r"^## \[(\d[^\]]*)\]", CHANGELOG.read_text(), re.M)]


def unreleased_body() -> str:
    m = re.search(r"^## \[Unreleased\]\n(.*?)(?=^## \[|\Z)", CHANGELOG.read_text(), re.M | re.S)
    return (m.group(1) if m else "").strip()


def shipped_version() -> str:
    m = re.search(VERSION_PATTERN, (ROOT / VERSION_FILE).read_text(), re.M)
    return m.group(1) if m else ""


def in_file(version: str) -> str:
    return VERSION_IN_FILE.format(version=version, major_minor=major_minor(version))


def set_version(path: Path, pattern: str, version: str) -> None:
    text = path.read_text()
    m = re.search(pattern, text, re.M)
    if not m:
        fail(f"{path.name}: nothing matches {pattern!r}")
    path.write_text(text[: m.start(1)] + version + text[m.end(1):])


def tags() -> list[str]:
    return [t for t in git("tag", "-l", "v[0-9]*", "--sort=-v:refname").splitlines() if t]


# ── the checks ───────────────────────────────────────────────────────────────────────


def check_tracked_files() -> None:
    tracked = git("ls-files").splitlines()
    leaked = [f for f in tracked if re.search(MUST_STAY_LOCAL, f)]
    if leaked:
        fail("tracked but must stay local: " + ", ".join(leaked))
    ok(f"nothing local is tracked ({len(tracked)} files)")


def check_denylist(since: str | None) -> None:
    if not DENYLIST.is_file():
        print("! no .release-denylist next to the repository: the forbidden-string check is skipped", file=sys.stderr)
        return
    patterns = [p.strip() for p in DENYLIST.read_text().splitlines() if p.strip() and not p.startswith("#")]
    if not patterns:
        ok("denylist is empty")
        return
    regex = re.compile("|".join(re.escape(p) for p in patterns), re.I)
    hits = []
    for path in git("ls-files").splitlines():
        try:
            text = (ROOT / path).read_text(errors="replace")
        except OSError:
            continue
        hits += [f"{path}:{n}" for n, line in enumerate(text.splitlines(), 1) if regex.search(line)]
    scope = f"{since}..HEAD" if since else "HEAD"
    for line in git("log", "-p", "--format=%H %s%n%b", scope, check=False).splitlines():
        if regex.search(line):
            hits.append(f"history {scope}: {line.strip()[:80]}")
            if len(hits) > 20:
                break
    if hits:
        fail("forbidden string(s) from .release-denylist found:\n  " + "\n  ".join(hits[:20]))
    ok(f"no forbidden string in the tree or in {scope} ({len(patterns)} pattern(s))")


def check_consistency() -> None:
    versions = changelog_versions()
    if not versions:
        fail("CHANGELOG.md has no released section")
    newest, current = versions[0], shipped_version()
    if current != in_file(newest):
        fail(f"{VERSION_FILE} ships {current or 'no version'}, but the newest changelog section is [{newest}]")
    ok(f"{VERSION_FILE} ships {current}, the newest changelog section")
    missing = [t for t in tags() if t.removeprefix("v") not in versions]
    if missing:
        fail("tagged, but not in CHANGELOG.md: " + ", ".join(missing))
    ok(f"every tag has a changelog section ({len(tags())} tags)")


def check_all() -> None:
    check_tracked_files()
    check_denylist(tags()[0] if tags() else None)
    check_consistency()


# ── the draft ────────────────────────────────────────────────────────────────────────

GROUPS = (
    ("Removed", r"^(remove|drop|delete|retire)\b"),
    ("Fixed", r"^(fix|refuse|repair|correct|guard)\b|\bbug\b"),
    ("Added", r"^(add|new|introduce|support)\b|\bnew\b"),
)
HOUSEKEEPING = r"^(docs?|page rev|readme|changelog|journal|version|tests?|ci)\b"


def draft_groups() -> tuple[str, dict[str, list[str]]]:
    """The newest tag, and the commits since it grouped as entry candidates."""
    latest = tags()[0] if tags() else ""
    span = f"{latest}..HEAD" if latest else "HEAD"
    log = git("log", "--no-merges", "--reverse", "--format=%h%x1f%s%x1f%b%x1e", span)
    commits = [(c.strip("\n").split("\x1f") + ["", ""])[:3] for c in log.split("\x1e") if c.strip()]
    groups: dict[str, list[str]] = {"Added": [], "Changed": [], "Fixed": [], "Removed": [], "housekeeping, probably no entry": []}
    for short, subject, body in commits:
        short, subject = short.strip(), subject.strip()
        first = next((ln.strip() for ln in body.strip().splitlines() if ln.strip() and not ln.startswith("Co-Authored-By")), "")
        line = f"- **{subject.rstrip('.')}.** ({short})" + (f" {first}" if first else "")
        if re.search(HOUSEKEEPING, subject, re.I):
            groups["housekeeping, probably no entry"].append(line)
            continue
        for name, pattern in GROUPS:
            if re.search(pattern, subject, re.I):
                groups[name].append(line)
                break
        else:
            groups["Changed"].append(line)
    return latest, groups


def draft() -> str:
    """The commits since the newest tag as entry candidates for [Unreleased], grouped."""
    latest, groups = draft_groups()
    if not any(groups.values()):
        return f"no commit since {latest or 'the beginning'}: nothing to draft"
    out = [f"# {sum(len(v) for v in groups.values())} commit(s) since {latest or 'the beginning'}, oldest first. Candidates, not entries:",
           "# rewrite each as what changed for the person using the tool, and why, under [Unreleased]."]
    for name, lines in groups.items():
        if lines:
            out += ["", f"### {name}", ""] + lines
    existing = unreleased_body()
    out += ["", "# already under [Unreleased]:" if existing else "# [Unreleased] is empty."]
    if existing:
        out += ["#   " + ln for ln in existing.splitlines()]
    return "\n".join(out)


def write_draft() -> int:
    """Put the candidates (housekeeping excluded) under [Unreleased], after what is there.
    Returns how many lines were written."""
    _latest, groups = draft_groups()
    blocks = [f"### {name}\n\n" + "\n".join(lines) for name, lines in groups.items()
              if lines and not name.startswith("housekeeping")]
    if not blocks:
        return 0
    text = CHANGELOG.read_text()
    m = re.search(r"^## \[Unreleased\]\n(.*?)(?=^## \[|\Z)", text, re.M | re.S)
    if not m:
        fail("CHANGELOG.md has no [Unreleased] section")
    body = (m.group(1).rstrip() + "\n\n" + "\n\n".join(blocks) + "\n\n").lstrip("\n")
    CHANGELOG.write_text(text[: m.start(1)] + "\n" + body + text[m.end(1):])
    return sum(len(b.splitlines()) for b in blocks)


# ── the cut ──────────────────────────────────────────────────────────────────────────


def cut(version: str, *, dry_run: bool, push: bool, from_commits: bool = False) -> None:
    version = version.removeprefix("v")
    if not re.fullmatch(VERSION_SHAPE, version):
        fail(f"'{version}' does not look like {VERSION_SHAPE}")
    if git("status", "--porcelain"):
        fail("the working tree is not clean; commit or stash first")
    if (branch := git("rev-parse", "--abbrev-ref", "HEAD")) != "main":
        fail(f"on branch {branch}, releases are cut from main")
    latest = tags()[0] if tags() else ""
    if latest and vkey(version) <= vkey(latest):
        fail(f"{version} is not above the newest tag {latest}")
    if version in changelog_versions():
        fail(f"CHANGELOG.md already has a [{version}] section")
    for template in REQUIRED_FILES:
        needed = template.format(version=version, major_minor=major_minor(version))
        if not (ROOT / needed).exists():
            fail(f"{needed} does not exist; create it before cutting {version}")
    if from_commits and not dry_run:
        written = write_draft()
        ok(f"[Unreleased] filled from the commits since {latest or 'the beginning'} ({written} line(s))")
    body = unreleased_body()
    if from_commits and dry_run:
        _l, groups = draft_groups()
        candidates = "\n\n".join(f"### {n}\n\n" + "\n".join(ls) for n, ls in groups.items() if ls and not n.startswith("housekeeping"))
        body = (body + "\n\n" + candidates).strip() if candidates else body
        ok(f"would fill [Unreleased] from the commits since {latest or 'the beginning'}")
    if not body:
        fail("CHANGELOG.md has an empty [Unreleased] section: nothing to release"
             + ("" if from_commits else " (write it, or cut with --from-commits)"))
    check_tracked_files()
    check_denylist(latest or None)

    heading = f"## [{version}] — {dt.date.today().isoformat()}"
    first = next((line.lstrip("- ").strip() for line in body.splitlines() if line.startswith("- ")), "")
    tag_message = f"{PROJECT} {version}" + (f": {re.sub(r'[*`]', '', first)[:100]}" if first else "")
    print(f"\n{heading}\n{body[:400]}{'…' if len(body) > 400 else ''}\n")
    if dry_run:
        print(f"dry run: would write {heading}, set {in_file(version)} in {VERSION_FILE}"
              + (f" and {', '.join(ALSO_UPDATE)}" if ALSO_UPDATE else "")
              + (f", run {' '.join(TEST_COMMAND)}" if TEST_COMMAND else "")
              + f", commit 'Release {version}', tag v{version}" + (", push main and the tag" if push else ""))
        return

    text = CHANGELOG.read_text().replace("## [Unreleased]\n", f"## [Unreleased]\n\n{heading}\n", 1)
    CHANGELOG.write_text(re.sub(r"\n{3,}", "\n\n", text))
    set_version(ROOT / VERSION_FILE, VERSION_PATTERN, in_file(version))
    for path, pattern in ALSO_UPDATE.items():
        set_version(ROOT / path, pattern, version)
    check_consistency()
    if TEST_COMMAND and subprocess.run(TEST_COMMAND, cwd=ROOT).returncode != 0:
        git("checkout", "--", ".")
        fail("tests failed: nothing released, files restored")

    git("add", "-A")
    git("commit", "-q", "-m", f"Release {version}")
    git("tag", "-a", f"v{version}", "-m", tag_message)
    ok(f"committed 'Release {version}' and tagged v{version}")
    if push:
        git("push", "origin", "main")
        git("push", "origin", f"v{version}")
        ok("pushed main and the tag; the release workflow publishes the note")
    else:
        print(f"next: git push origin main v{version}   (or re-run with --push)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("version", nargs="?", help="the version to cut")
    parser.add_argument("--check", action="store_true", help="run the release-time checks and exit")
    parser.add_argument("--draft", action="store_true", help="print the commits since the last tag as entry candidates")
    parser.add_argument("--write", action="store_true", help="with --draft: write the candidates under [Unreleased]")
    parser.add_argument("--from-commits", action="store_true", help="with a version: fill [Unreleased] from the commits, then cut")
    parser.add_argument("--dry-run", action="store_true", help="show what a cut would do")
    parser.add_argument("--push", action="store_true", help="push main and the tag after cutting")
    args = parser.parse_args(argv)
    if args.check:
        check_all()
        return 0
    if args.draft:
        print(draft())
        if args.write:
            n = write_draft()
            print(f"\nwrote {n} line(s) under [Unreleased] in CHANGELOG.md; edit, then cut" if n else "\nnothing to write")
        return 0
    if not args.version:
        parser.error("name a version, or pass --check or --draft")
    cut(args.version, dry_run=args.dry_run, push=args.push, from_commits=args.from_commits)
    return 0


if __name__ == "__main__":
    sys.exit(main())
