import typer

app = typer.Typer(help="Manage profiles")


@app.command()
def list():
    """
    List profiles
    """
    print("Listing profiles")
