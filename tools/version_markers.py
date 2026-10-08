#!/usr/bin/env python3
"""The nine places a zpodcore version is written, and whether they agree. Standard library only.

    python3 tools/version_markers.py           # print each marker
    python3 tools/version_markers.py --check   # print the version if all agree, exit 1 otherwise

tools/release.py moves all of them at a cut (VERSION_FILE plus ALSO_UPDATE); this is the
between-releases check that nothing moved one of them by hand. CI runs it on every push.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MARKERS: dict[str, str] = {
    "zpodapi/src/zpodapi/__init__.py": r'^__version__ = "([^"]+)"',
    "zpodcli/src/zpodcli/__init__.py": r'^__version__ = "([^"]+)"',
    "zpodengine/src/zpodengine/__init__.py": r'^__version__ = "([^"]+)"',
    "zpodsdk/src/zpodsdk/__init__.py": r'^__version__ = "([^"]+)"',
    "zpodapi/pyproject.toml": r'^version = "([^"]+)"',
    "zpodcli/pyproject.toml": r'^version = "([^"]+)"',
    "zpodengine/pyproject.toml": r'^version = "([^"]+)"',
    "zpodsdk/pyproject.toml": r'^version = "([^"]+)"',
    "zpodsdk_builder/pyproject.toml": r'^version = "([^"]+)"',
}
# The SDK requirement in zpodcli: `~=` means "this version or a later patch of it", so it is
# allowed to trail the version during a package-scoped zpodcli release, never to lead it.
SDK_REQUIREMENT = ("zpodcli/pyproject.toml", r'^    "zpodsdk~=([^"]+)",')


def read(path: str, pattern: str) -> str:
    m = re.search(pattern, (ROOT / path).read_text(), re.M)
    return m.group(1) if m else ""


def main(argv: list[str]) -> int:
    found = {path: read(path, pattern) for path, pattern in MARKERS.items()}
    sdk_req = read(*SDK_REQUIREMENT)
    if "--check" not in argv:
        for path, version in found.items():
            print(f"{version or '(missing)':10} {path}")
        print(f"{sdk_req or '(missing)':10} {SDK_REQUIREMENT[0]} (zpodsdk~=)")
        return 0
    versions = set(found.values())
    if len(versions) != 1 or "" in versions:
        for path, version in found.items():
            print(f"  {version or '(missing)':10} {path}", file=sys.stderr)
        return 1
    (version,) = versions
    if not sdk_req:
        print(f"  zpodcli/pyproject.toml: no 'zpodsdk~=' requirement", file=sys.stderr)
        return 1
    print(version)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
