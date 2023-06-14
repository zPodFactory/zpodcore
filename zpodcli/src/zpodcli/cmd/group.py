import typer

app = typer.Typer(help="Manage endpoints")


@app.command(name="list")
def _list():
    """
    List Groups
    """
    print("Listing groups")
