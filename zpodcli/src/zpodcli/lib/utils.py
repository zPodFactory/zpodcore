import typer
from rich import print
from rich.prompt import Confirm


def exit_with_error(txt, code=1, color="indian_red"):
    print_errors(txt, color)
    raise typer.Exit(code)


def print_errors(txt, color="indian_red"):
    print(f"[{color}]Error(s) Found:\n  {txt}[/{color}]")


def get_boolean_markdown(boolean: bool):
    if boolean:
        return f"[dark_sea_green4]{boolean}[/dark_sea_green4]"
    return f"[indian_red]{boolean}[/indian_red]"


def confirm(msg="Are you sure?"):
    if not Confirm.ask(msg):
        raise typer.Abort()
