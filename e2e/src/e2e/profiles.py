"""Profile fixture loading.

Fixture files under tests/fixtures/profiles/*.json hold the raw `profile`
array only (see tests/fixtures/profiles/README.md) - this module turns
that JSON into ready-to-use ProfileCreate.profile items by reusing the
SDK's own parsing (ProfileCreate.from_dict), rather than hand-rolling it.
"""

import json
from pathlib import Path

from zpodsdk.models.profile_create import ProfileCreate


def load_profile_items(path: Path) -> list:
    raw = json.loads(path.read_text())
    parsed = ProfileCreate.from_dict({"name": "_placeholder", "profile": raw})
    return parsed.profile


def discover_profile_files(profiles_dir: Path) -> list[Path]:
    if not profiles_dir.is_dir():
        return []
    return sorted(p for p in profiles_dir.glob("*.json"))


def profile_body(name: str, items: list):
    """A ProfileCreate body from plain JSON profile items.

    zpodsdk 0.9 serializes only typed ProfileItemCreate objects; from_dict
    builds them (and the nested lists for parallel items). Accepts plain
    dicts or items already parsed by load_profile_items.
    """
    def plain(item):
        if isinstance(item, list):
            return [plain(i) for i in item]
        return item.to_dict() if hasattr(item, "to_dict") else item

    return ProfileCreate.from_dict({"name": name, "profile": [plain(i) for i in items]})
