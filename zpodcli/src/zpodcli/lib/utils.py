import typer
from rich import print
from rich.console import Console
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


# Prints Rich Console object.
# if global SVG flag is True, will generate SVG output file.
def console_print(title, content):
    console = Console(record=GLOBAL_FLAGS["svg"])
    console.print(content)
    if GLOBAL_FLAGS["svg"]:
        filename = title.replace(" ", "_").lower() + ".svg"
        console.save_svg(filename, title="", theme=DIMMED_MONOKAI)
