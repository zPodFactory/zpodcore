import typer

app = typer.Typer(help="Manage permissions")


@app.command(name="list")
def _list():
    """
    List permissions
    """
    print("Listing permissions")
