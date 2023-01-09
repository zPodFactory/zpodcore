import typer

from zpodcli.lib.callback import isauthenticated

app = typer.Typer(help="Manage pods", callback=isauthenticated)


@app.command()
def list():
    """
    List pods
    """
    print("Listing pods")
