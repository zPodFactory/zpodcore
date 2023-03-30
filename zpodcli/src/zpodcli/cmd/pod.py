import typer

app = typer.Typer(help="Manage pods")


@app.command()
def list():
    """
    List pods
    """
    print("Listing pods")
