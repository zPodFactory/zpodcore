import typer
from rich import print

from zpodcli.cmd import (
    component,
    connect,
    endpoint,
    group,
    library,
    permission,
    pod,
    profile,
    user,
)

app = typer.Typer()


def launch():
    # top level commands
    app.command()(connect.connect)
    # own level commands

    app.add_typer(group.app, name="group")
    app.add_typer(pod.app, name="pod")
    app.add_typer(profile.app, name="profile")
    app.add_typer(library.app, name="library")
    app.add_typer(permission.app, name="permission")
    app.add_typer(endpoint.app, name="endpoint")
    app.add_typer(component.app, name="component")
    app.add_typer(user.app, name="user")

    app()


@app.command()
def version():
    print("0.1.0")


if __name__ == "__main__":
    launch()
