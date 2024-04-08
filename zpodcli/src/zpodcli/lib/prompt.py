from typing import Any, List, Optional, TextIO

import typer
from rich import print
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.text import TextType


def ask(
    prompt: TextType = "",
    *,
    console: Optional[Console] = None,
    password: bool = False,
    choices: Optional[List[str]] = None,
    show_default: bool = True,
    show_choices: bool = True,
    default: Any = ...,
    stream: Optional[TextIO] = None,
    validation: None = None,
):
    while 1:
        inp = Prompt.ask(
            prompt=prompt,
            console=console,
            password=password,
            choices=choices,
            show_default=show_default,
            show_choices=show_choices,
            default=default,
            stream=stream,
        )
        if not validation or validation(inp):
            return inp
        print("[red]Invalid.  Try again.[/red]")


def confirm(msg="Are you sure?"):
    if not Confirm.ask(msg):
        raise typer.Abort()
