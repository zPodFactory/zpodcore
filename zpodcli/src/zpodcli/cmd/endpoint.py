import typer

app = typer.Typer(help="Manage endpoints")


@app.command()
def list():
    """
    List Endpoints
    """
    print("Listing endpoints")
