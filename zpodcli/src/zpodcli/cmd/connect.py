import typer
from rich import print
from typing_extensions import Annotated

from zpodcli.lib.config import config

app = typer.Typer(help="Manage zPod Manager Connection")


@app.callback(invoke_without_command=True)
def connect(
    server: Annotated[
        str,
        typer.Option("--server", "-s"),
    ],
    token: Annotated[
        str,
        typer.Option("--token", "-t"),
    ],
):
    """
    Manage zPod Manager connection
    """
    print(f"Setting Server connection to {server} with api_token {token}...")

    cfg = config()
    cfg.setup(server, token)
