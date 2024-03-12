from functools import partial
from typing import Optional

import typer
from rich import print
from typing_extensions import Annotated

from zpodcli import __version__
from zpodcli.cmd import (
    component,
    endpoint,
    enet,
    factory,
    instance,
    library,
    permission_group,
    profile,
    setting,
    user,
)
from zpodcli.lib.global_flags import GLOBAL_FLAGS

app = typer.Typer(no_args_is_help=True)


def version_callback(value: bool):
    if value:
        typer.echo(f"zcli version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    factory: Annotated[
        Optional[str],
        typer.Option(
            "--factory",
            "-f",
            help="Use specified factory for current commmand.",
            show_default=False,
        ),
    ] = None,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-V",
            help="Display version information.",
            callback=version_callback,
        ),
    ] = None,
):
    GLOBAL_FLAGS["factory"] = factory


def launch():
    child_typer = partial(app.add_typer, no_args_is_help=True)

    # commands
    child_typer(component.app, name="component")
    child_typer(endpoint.app, name="endpoint")
    child_typer(enet.app, name="enet")
    child_typer(factory.app, name="factory")
    child_typer(permission_group.app, name="group")
    child_typer(instance.app, name="instance")
    child_typer(library.app, name="library")
    child_typer(profile.app, name="profile")
    child_typer(setting.app, name="setting")
    child_typer(user.app, name="user")

    app()


if __name__ == "__main__":
    launch()
