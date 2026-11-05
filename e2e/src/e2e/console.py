"""Rich-based console output.

Test files call these helpers instead of raw `rich` so output stays
consistent across the suite. Plain rich, not a textual TUI: pytest owns the
terminal and the output has to stay readable in CI logs.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def banner(title: str, description: str, **resources: str) -> None:
    """Printed at the start of a test: title, description, and the
    resources it's about to touch (zpod name, profile, role, ...).
    """
    body = description
    if resources:
        body += "\n\n" + "\n".join(f"[dim]{k}:[/dim] {v}" for k, v in resources.items())
    console.print(Panel(body, title=title, border_style="cyan"))


def result_table(results: list[dict]) -> None:
    """`results`: list of {"name", "outcome", "duration", "detail"} dicts."""
    table = Table(title="e2e run summary")
    table.add_column("Test")
    table.add_column("Outcome")
    table.add_column("Duration", justify="right")
    table.add_column("Detail")

    outcome_style = {"passed": "green", "failed": "red", "skipped": "yellow"}
    for r in results:
        style = outcome_style.get(r["outcome"], "white")
        table.add_row(
            r["name"],
            f"[{style}]{r['outcome']}[/{style}]",
            f"{r['duration']:.1f}s",
            r.get("detail", ""),
        )
    console.print(table)
