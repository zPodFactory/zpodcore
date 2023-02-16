import typer
from rich import print
from rich.console import Console
from rich.table import Table

from zpodcli.lib import zpod_client
from zpodcli.lib.callback import isauthenticated

app = typer.Typer(help="Manage libraries", callback=isauthenticated)


@app.command()
def list():
    """
    List libraries
    """
    print("Listing libraries")

    z = zpod_client.ZpodClient()
    libraries = z.libraries_get_all.sync()

    print("Server Library list")
    print(libraries)

    print("")
    print("[yellow][blink]Rich Table nice view ;-)[/blink][/yellow]")

    table = Table(title="Library List", show_header=True, header_style="bold cyan")
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Git URL")
    table.add_column("Creation Date")
    table.add_column("Last Update")
    table.add_column("Enabled")

    for library in libraries:
        table.add_row(
            library.name,
            library.description,
            library.git_url,
            library.creation_date.strftime("%Y-%m-%d %H:%M:%S"),
            library.lastupdate_date.strftime("%Y-%m-%d %H:%M:%S"),
            library.enabled.__str__(),
        )

    console = Console()
    console.print(table)
