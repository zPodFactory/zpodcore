import typer

from zpodcli.lib.callback import isauthenticated

app = typer.Typer(help="Manage endpoints", callback=isauthenticated)


@app.command()
def list():
    """
    List Endpoints
    """
    print("Listing endpoints")
