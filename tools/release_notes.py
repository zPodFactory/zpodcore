#!/usr/bin/env python3
"""The changelog section a version already has, published as the GitHub release note.

A tag is a name for a commit, not a release note. The notes are read from `CHANGELOG.md`
rather than written a second time: a changelog that exists twice disagrees with itself by
the next release, and the copy people actually edit is the file.

    python3 tools/release_notes.py 0.3.0             # print what would be published
    python3 tools/release_notes.py 0.3.0 --publish   # create it, or update it
    python3 tools/release_notes.py --all --publish   # every tag that has a section
    python3 tools/release_notes.py --check           # every tag has one

Tagging stays a human action: `--publish` passes `--verify-tag`, so this fills in a release
for a tag that exists and can never invent the tag itself. `.github/workflows/release.yml`
runs the same command when a tag is pushed, which is what makes "every tag gets its notes"
hold without anybody remembering a second command. Standard library only.

Copied from tsugliani/zcli-vsphere (MIT). The block below is the only part that differs
between repositories.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"


# ── per-repository configuration ─────────────────────────────────────────────────────

PACKAGES = ("zpodsdk", "zpodcli")                  # published to PyPI from the same tag


def facts(version: str) -> str:
    """What a zpodcore version is and where to get each part, above the changelog section:
    the stack from the tag, zcli and zpodsdk from PyPI. The release workflow publishes both
    wheels from the same tag and attaches them to the GitHub release."""
    mm = ".".join(version.split(".")[:2])
    rows = [
        "| | |", "|---|---|",
        f"| Stack | `just zpod-update {version}` — coming from 0.7.x, read **Upgrading** in README.md first |",
        f"| zcli | `uv tool install zpodcli=={version}` — https://pypi.org/project/zpodcli/{version}/ |",
        f"| zpodsdk | `uv add zpodsdk=={version}` — https://pypi.org/project/zpodsdk/{version}/ |",
    ]
    return (
        f"zpodcore {version}: the zPod API, the zPod Engine (Prefect flows), `zcli` and `zpodsdk`, "
        "all at the same version.\n\n" + "\n".join(rows) + "\n\n"
        "Docker images are built from the checkout; there is no registry image. "
        f"zcli {mm}.x and zpodsdk {mm}.x are matched with API {mm}.x."
    )
# ─────────────────────────────────────────────────────────────────────────────────────

_TOKEN_FALLBACK_SAID = False


# ── the file ─────────────────────────────────────────────────────────────────────────


def sections() -> dict[str, tuple[str, str]]:
    """version → (date, body), newest first, skipping `[Unreleased]` and empty ones."""
    out: dict[str, tuple[str, str]] = {}
    text = CHANGELOG.read_text()
    heads = list(re.finditer(r"^## \[([^\]]+)\](?:\s*[—-]+\s*(.*))?$", text, re.M))
    for index, head in enumerate(heads):
        end = heads[index + 1].start() if index + 1 < len(heads) else len(text)
        version, date = head.group(1), (head.group(2) or "").strip()
        body = text[head.end():end].strip()
        if re.match(r"^\d", version) and body:
            out[version] = (date, body)
    return out


# ── git and GitHub ───────────────────────────────────────────────────────────────────


def _git(*args: str, check: bool = True) -> str:
    done = subprocess.run(("git", *args), cwd=ROOT, capture_output=True, text=True)
    if check and done.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{done.stderr.strip()}")
    return done.stdout.strip()


def version_key(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", text))


def tags() -> list[str]:
    """Release tags, oldest first. Empty when there is no git or no tags."""
    listing = _git("tag", "-l", "v[0-9]*", check=False)
    return sorted((line for line in listing.splitlines() if line), key=version_key)


def previous_tag(version: str) -> str:
    older = [tag for tag in tags() if version_key(tag) < version_key(version)]
    return max(older, key=version_key) if older else ""


def repo_slug() -> str:
    """`owner/name`, read from the remote rather than asked of the network."""
    url = _git("remote", "get-url", "origin", check=False)
    match = re.search(r"github\.com[:/](?P<slug>[^/]+/[^/]+?)(?:\.git)?$", url)
    return match.group("slug") if match else ""


def _gh(*args: str) -> subprocess.CompletedProcess:
    """`gh`, with one workaround: an invalid GITHUB_TOKEN shadows a working `gh auth login`.

    `gh` prefers `GITHUB_TOKEN`/`GH_TOKEN` over the credential it stored at login, so an
    expired token exported in a shell turns every call into `401 Bad credentials` while
    `gh auth status` reports a logged-in account underneath it. The retry is announced
    rather than silent: a workaround nobody sees is a token nobody fixes.
    """
    global _TOKEN_FALLBACK_SAID
    first = subprocess.run(("gh", *args), cwd=ROOT, capture_output=True, text=True)
    if first.returncode == 0:
        return first
    said = (first.stderr or "") + (first.stdout or "")
    shadowed = any(name in os.environ for name in ("GITHUB_TOKEN", "GH_TOKEN"))
    if not shadowed or not re.search(r"Bad credentials|401|gh auth login", said):
        return first
    env = {k: v for k, v in os.environ.items() if k not in ("GITHUB_TOKEN", "GH_TOKEN")}
    retry = subprocess.run(("gh", *args), cwd=ROOT, capture_output=True, text=True, env=env)
    if retry.returncode == 0 and not _TOKEN_FALLBACK_SAID:
        _TOKEN_FALLBACK_SAID = True
        print("note: the GITHUB_TOKEN in this environment is not valid; used the stored "
              "`gh auth login` credential instead", file=sys.stderr)
    return retry


def release_exists(tag: str) -> bool:
    return _gh("release", "view", tag, "--json", "tagName").returncode == 0


# ── what gets published ──────────────────────────────────────────────────────────────


def title_for(version: str) -> str:
    """The tag, and nothing else: a list of releases is read as a list of versions."""
    return f"v{version}"


def notes_for(version: str) -> str:
    """The release body: the facts, the section as written, and the two links."""
    found = sections()
    if version not in found:
        raise SystemExit(f"CHANGELOG.md has no section for {version}; write it first")
    _date, body = found[version]
    footer = []
    if slug := repo_slug():
        if previous := previous_tag(version):
            footer.append(f"**Full changelog**: https://github.com/{slug}/compare/{previous}...v{version}")
        footer.append(f"**Every release**: https://github.com/{slug}/blob/main/CHANGELOG.md")
    # Blank lines between the footer links: two lines with one newline between them are one
    # markdown paragraph. No date line: GitHub prints the date beside the tag already.
    parts = (facts(version), body, "\n\n".join(footer))
    return "\n\n".join(part for part in parts if part) + "\n"


def publish(version: str, *, newest: bool) -> str:
    """Create the release, or bring an existing one's notes back in line with the file."""
    tag = f"v{version}"
    if tag not in tags():
        raise SystemExit(f"{tag} is not a tag: tag the release first, then publish it")
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as handle:
        handle.write(notes_for(version))
        path = handle.name
    try:
        if release_exists(tag):
            done = _gh("release", "edit", tag, "--notes-file", path, "--title", title_for(version))
            verb = "updated"
        else:
            # Never as a side effect: a missing tag is a mistake to report, not a tag to create.
            done = _gh("release", "create", tag, "--verify-tag", "--title", title_for(version),
                       "--notes-file", path, "--latest" if newest else "--latest=false")
            verb = "created"
    finally:
        os.unlink(path)
    if done.returncode != 0:
        raise SystemExit(f"gh failed for {tag}:\n{done.stderr.strip()}")
    return f"{verb} {tag}: {done.stdout.strip() or title_for(version)}"


# ── the check the test and CI run ────────────────────────────────────────────────────


def missing_sections() -> list[str]:
    """Tags with no changelog section. The rule, in one function, so a test can call it."""
    found = sections()
    return [tag for tag in tags() if tag.removeprefix("v") not in found]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("version", nargs="?", help="e.g. 0.3.0 (or v0.3.0)")
    parser.add_argument("--all", action="store_true", help="every tag that has a changelog section")
    parser.add_argument("--publish", action="store_true", help="write it to GitHub with gh, instead of printing it")
    parser.add_argument("--check", action="store_true", help="exit non-zero if any tag has no changelog section")
    args = parser.parse_args(argv)

    if args.check:
        gaps = missing_sections()
        if gaps:
            print("tagged, but not in CHANGELOG.md: " + ", ".join(gaps), file=sys.stderr)
            return 1
        print(f"every tag has a changelog section ({len(tags())} tags)")
        return 0

    if args.all:
        wanted = [t.removeprefix("v") for t in tags() if t.removeprefix("v") in sections()]
    elif args.version:
        wanted = [args.version.removeprefix("v")]
    else:
        parser.error("name a version, or pass --all or --check")

    newest = tags()[-1].removeprefix("v") if tags() else ""
    for version in wanted:
        if not args.publish:
            print(f"── {title_for(version)}\n\n{notes_for(version)}")
            continue
        print(publish(version, newest=(version == newest)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
