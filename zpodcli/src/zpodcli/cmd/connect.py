import typer
from rich import print

from zpodcli.lib.config import config


def connect(
    server: str = typer.Option(..., "--server", "-s"),
    token: str = typer.Option(..., "--token", "-t"),
):
    """
    Manage zPod Manager connection
    """
    print(f"Setting Server connection to {server} with api_token {token}...")

    cfg = config()
    cfg.setup(server, token)
