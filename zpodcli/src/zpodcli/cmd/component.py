import typer

from zpodcli.lib.callback import isauthenticated

app = typer.Typer(help="Manage components", callback=isauthenticated)


@app.command()
def list():
    """
    List components
    """
    print("Listing components")
