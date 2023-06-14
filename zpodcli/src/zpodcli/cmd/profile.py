import typer

app = typer.Typer(help="Manage profiles")


@app.command(name="list")
def _list():
    """
    List profiles
    """
    print("Listing profiles")
