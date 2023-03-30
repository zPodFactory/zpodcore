import typer

app = typer.Typer(help="Manage permissions")


@app.command()
def list():
    """
    List permissions
    """
    print("Listing permissions")
