"""Per-test narrative metadata for the HTML report - purely decorative,
never read by the tests themselves.

A test's docstring already answers "what does this check." An `Insight`
answers the next question a human reading a test-suite result actually
asks: *why does this behave this way, and why is that worth checking?*
Same idea as a tester's own notes attached to a manual test case - the
reasoning that makes a non-obvious expected result make sense, and,
where there's a real cause-and-effect chain behind it, the chain itself
(a permission check resolving through a filtered query, a component
conflict cascading into a deploy failure, a toggle breaking a data path
three layers down) instead of just a pass/fail line.

Usage - a test module defines a module-level dict keyed by test function
name:

    from e2e.insight import Beat, Insight

    INSIGHTS = {
        "test_zpod_permission_no_grant_denied": Insight(
            why="A user with zero permission shouldn't even learn a zpod exists.",
            reasoning="get_zpod's query is permission-filtered for non-superadmins, "
                      "so a zero-grant lookup returns nothing before the "
                      "zpod_maintainer/zpod_reader dependency (which would 401) ever runs.",
            expected="Both read and write return 404, not 401 - invisible, not just forbidden.",
            beats=[
                Beat("GET /zpods/{id}", "zero-grant user reads a zpod", state="404", color="pass", tag="WHAT YOU SEE"),
                Beat("permission-filtered query", "row never returned for this user", state="", color="info", tag="THE CLUE"),
                Beat("DELETE /zpods/{id}", "same 404 - consistent, not a fluke", state="404", color="pass"),
            ],
        ),
    }

`conftest.py`'s `_auto_banner` fixture looks this dict up automatically by
module + function name - nothing else to wire up. Not every test needs
one; add it where the "why" isn't obvious from the docstring alone, or
where the actual cause-and-effect chain is more convincing than a wall of
prose.
"""

from dataclasses import dataclass, field


@dataclass
class Beat:
    """One step in a cause-and-effect chain, rendered as a small card in a
    left-to-right cascade strip: a status pill, a short label, one line of
    concrete detail, and an optional callout tag marking the narratively
    important step (e.g. "WHAT YOU SEE", "THE CLUE", "ROOT CAUSE", "DEAD END").
    """

    label: str
    detail: str
    state: str = ""
    color: str = "info"  # pass | fail | skip | info
    tag: str = ""


@dataclass
class Insight:
    """The narrative behind one test: why it exists, the reasoning that
    makes its expected outcome non-obvious, what "success" actually means,
    and - optionally - the cause-and-effect chain that led to it."""

    why: str
    reasoning: str = ""
    expected: str = ""
    beats: list[Beat] = field(default_factory=list)
