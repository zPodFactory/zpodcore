from functools import partial
from typing import Optional

import typer
from typing_extensions import Annotated

from zpodcli import __version__
from zpodcli.cmd import (
    component_cli,
    endpoint_cli,
    enet_cli,
    factory_cli,
    library_cli,
    permission_group_cli,
    profile_cli,
    setting_cli,
    user_cli,
    zpod_cli,
)
from zpodcli.lib.global_flags import GLOBAL_FLAGS

app = typer.Typer(
    no_args_is_help=True,
)


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
            help="Use specified factory for current command.",
            show_default=False,
        ),
    ] = None,
    svg: Annotated[
        Optional[bool],
        typer.Option(
            "--output-svg",
            help="Output an SVG file for any list command.",
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
    GLOBAL_FLAGS["svg"] = svg


def launch():
    child_typer = partial(app.add_typer, no_args_is_help=True)

    # commands
    child_typer(component_cli.app, name="component")
    child_typer(endpoint_cli.app, name="endpoint")
    child_typer(enet_cli.app, name="enet")
    child_typer(factory_cli.app, name="factory")
    child_typer(permission_group_cli.app, name="group")
    child_typer(library_cli.app, name="library")
    child_typer(profile_cli.app, name="profile")
    child_typer(setting_cli.app, name="setting")
    child_typer(user_cli.app, name="user")
    child_typer(zpod_cli.app, name="zpod")

    app()


if __name__ == "__main__":
    launch()
