import typer

from zpodcli.lib.callback import isauthenticated

app = typer.Typer(help="Manage permissions", callback=isauthenticated)


@app.command()
def list():
    """
    List permissions
    """
    print("Listing permissions")
