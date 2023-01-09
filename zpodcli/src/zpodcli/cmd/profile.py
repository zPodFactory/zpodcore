import typer

from zpodcli.lib.callback import isauthenticated

app = typer.Typer(help="Manage profiles", callback=isauthenticated)


@app.command()
def list():
    """
    List profiles
    """
    print("Listing profiles")
