import json
import os
import sys
from typing import Annotated

import typer
from rich import print
from rich.console import Console
from rich.json import JSON
from rich.table import Table

from zpodcli.lib.catppuccin_mocha import CATPPUCCIN_MOCHA_TERMINAL
from zpodcli.lib.global_flags import GLOBAL_FLAGS

DEFAULT_SVG_WIDTH = 240
DEFAULT_SVG_MIN_WIDTH = 200


class ZcliTable(Table):
    """Rich table tuned for SVG screenshots (no wrap/truncation)."""

    def __init__(self, *args, **kwargs):
        if GLOBAL_FLAGS["svg"]:
            kwargs.setdefault("expand", False)
        super().__init__(*args, **kwargs)

    def add_column(self, *args, **kwargs):
        if GLOBAL_FLAGS["svg"]:
            kwargs.setdefault("no_wrap", True)
            kwargs.setdefault("overflow", "ignore")
        return super().add_column(*args, **kwargs)


def _svg_console_width() -> int:
    width = int(os.environ.get("ZCLI_SVG_WIDTH", str(DEFAULT_SVG_WIDTH)))
    return max(width, DEFAULT_SVG_MIN_WIDTH)


def _set_no_color(value: bool) -> bool:
    GLOBAL_FLAGS["no_color"] = value
    return value


# Shared output options for read commands (list/get/info).
# Usage: `json_: JsonOption = False, no_color: NoColorOption = False`
JsonOption = Annotated[
    bool,
    typer.Option(
        "--json",
        "-j",
        help="Display using json",
    ),
]

# The callback stores the flag in GLOBAL_FLAGS so console_print/json_print
# honor it without every command threading the value through.
NoColorOption = Annotated[
    bool,
    typer.Option(
        "--no-color",
        help="Disable color output",
        callback=_set_no_color,
    ),
]


def exit_with_error(txt, code=1, color="indian_red"):
    print_errors(txt, color)
    raise typer.Exit(code)


def print_errors(txt, color="indian_red"):
    print(f"[{color}]Error(s) Found:\n  {txt}[/{color}]")


def get_boolean_markdown(boolean: bool):
    if boolean:
        return f"[dark_sea_green4]{boolean}[/dark_sea_green4]"
    return f"[indian_red]{boolean}[/indian_red]"


def get_status_markdown(status: str):
    """Get status markdown with appropriate color coding

    Args:
        status: The status string to format
    """
    match status:
        case "ACTIVE":
            return f"[dark_sea_green4]{status}[/dark_sea_green4]"
        case "PENDING" | "BUILDING" | "POST_SCRIPTS" | "CONFIG_SCRIPTS":
            return f"[grey63]{status}...[/grey63]"
        case "DELETING":
            return f"[orange3]{status}...[/orange3]"
        case "DELETED":
            return f"[dark_orange3]{status}[/dark_orange3]"
        case "DEPLOY_FAILED" | "DESTROY_FAILED" | "ADD_FAILED" | "DELETE_FAILED":
            return f"[indian_red]{status}[/indian_red]"
        case _:
            return "[royal_blue1]UNKNOWN[/royal_blue1]"


# Prints Rich Console object.
# if global SVG flag is True, will generate SVG output file.
# if --no-color was given, colors are stripped (bold/dim styling is kept).
def console_print(title, content):
    if GLOBAL_FLAGS["svg"]:
        width = _svg_console_width()
        # Rich only honors `width` when `height` is also set (non-TTY environments).
        console = Console(record=True, width=width, height=80, soft_wrap=False)
    else:
        console = Console(no_color=GLOBAL_FLAGS["no_color"])
    console.print(content)
    if GLOBAL_FLAGS["svg"]:
        filename = title.replace(" ", "_").lower() + ".svg"
        console.save_svg(filename, title="", theme=CATPPUCCIN_MOCHA_TERMINAL)


def json_print(data):
    """Print JSON data.

    On a terminal, Rich pretty-prints with syntax colors. When stdout is not a
    TTY (piped to jq, redirected to a file) or --no-color was given, plain
    json.dumps output is written instead: Rich wraps long values at the console
    width when not attached to a terminal, which produces invalid JSON.

    Args:
        data: The data to print as JSON
    """
    if GLOBAL_FLAGS["no_color"] or not sys.stdout.isatty():
        sys.stdout.write(json.dumps(data, sort_keys=True) + "\n")
    else:
        print(JSON.from_data(data, sort_keys=True))
