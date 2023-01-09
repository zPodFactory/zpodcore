import typer

from zpodcli.lib.callback import isauthenticated

app = typer.Typer(help="Manage libraries", callback=isauthenticated)


@app.command()
def list():
    """
    List libraries
    """
    print("Listing libraries")
