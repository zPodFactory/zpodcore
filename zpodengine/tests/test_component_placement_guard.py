"""PROTECTED_COMPONENTS must list exactly the components with their own
branch in zpod_component_add_deploy: those branches never read `nested` or
`network`, so a component missing from the list would have them silently ignored."""

import ast
from pathlib import Path

from zpodcommon.lib.component_placement import PROTECTED_COMPONENTS
from zpodengine.zpod_component_add import zpod_component_add_3_deploy


def dedicated_branches() -> set[str]:
    """Component names in the `match component.component_name:` cases."""
    tree = ast.parse(Path(zpod_component_add_3_deploy.__file__).read_text())
    names = set()
    for match in ast.walk(tree):
        if not (
            isinstance(match, ast.Match)
            and ast.unparse(match.subject) == "component.component_name"
        ):
            continue
        for case in match.cases:
            for pattern in ast.walk(case.pattern):
                if isinstance(pattern, ast.MatchValue):
                    names.add(pattern.value.value)
    return names


def test_protected_components_match_the_deploy_branches():
    branches = dedicated_branches()
    assert branches, "no `match component.component_name:` found"
    assert branches == PROTECTED_COMPONENTS, (
        f"missing from PROTECTED_COMPONENTS: "
        f"{sorted(branches - PROTECTED_COMPONENTS)}; "
        f"no deploy branch: {sorted(PROTECTED_COMPONENTS - branches)}"
    )
