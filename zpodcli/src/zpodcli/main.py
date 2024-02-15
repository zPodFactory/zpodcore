from functools import partial

import typer
from rich import print

from zpodcli import __version__
from zpodcli.cmd import (
    component,
    connect,
    endpoint,
    enet,
    instance,
    library,
    permission_group,
    profile,
    setting,
    user,
)
from zpodcli.lib.callback import isauthenticated

app = typer.Typer(no_args_is_help=True)


def launch():
    # top level commands
    app.add_typer(
        connect.app,
        name="connect",
        no_args_is_help=True,
    )

    # own level commands
    authed_typer = partial(
        app.add_typer,
        callback=isauthenticated,
        no_args_is_help=True,
    )

    authed_typer(component.app, name="component")
    authed_typer(endpoint.app, name="endpoint")
    authed_typer(enet.app, name="enet")
    authed_typer(instance.app, name="instance")
    authed_typer(library.app, name="library")
    authed_typer(permission_group.app, name="group")
    authed_typer(profile.app, name="profile")
    authed_typer(setting.app, name="setting")
    authed_typer(user.app, name="user")

    app()


@app.command(help="Display Version")
def version():
    print(__version__)


if __name__ == "__main__":
    launch()
