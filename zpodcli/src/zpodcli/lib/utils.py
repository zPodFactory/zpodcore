import json
import sys

import typer
from rich import print
from rich.console import Console
from rich.json import JSON
from rich.terminal_theme import DIMMED_MONOKAI

from zpodcli.lib.global_flags import GLOBAL_FLAGS


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
def console_print(title, content):
    console = Console(record=GLOBAL_FLAGS["svg"])
    console.print(content)
    if GLOBAL_FLAGS["svg"]:
        filename = title.replace(" ", "_").lower() + ".svg"
        console.save_svg(filename, title="", theme=DIMMED_MONOKAI)


def json_print(data, no_color=False):
    """Print JSON data with optional color formatting

    Args:
        data: The data to print as JSON
        no_color: If True, print without color formatting
    """
    if no_color:
        sys.stdout.write(json.dumps(data, sort_keys=True) + "\n")
    else:
        print(JSON.from_data(data, sort_keys=True))
