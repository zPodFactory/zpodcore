import typer

app = typer.Typer(help="Manage endpoints")


@app.command()
def list():
    """
    List Groups
    """
    print("Listing groups")
