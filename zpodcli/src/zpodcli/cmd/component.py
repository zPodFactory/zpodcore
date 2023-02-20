import typer
from rich import print
from rich.console import Console
from rich.table import Table

from zpodcli.lib import zpod_client
from zpodcli.lib.callback import isauthenticated

app = typer.Typer(help="Manage components", callback=isauthenticated)


@app.command()
def list():
    """
    List components
    """
    print("Listing components")

    z = zpod_client.ZpodClient()
    components = z.components_get_all.sync()

    print("Server Component list")
    print(components)

    print("")
    print("[yellow][blink]Rich Table nice view ;-)[/blink][/yellow]")

    table = Table(title="Component List", show_header=True, header_style="bold cyan")
    table.add_column("Library")
    table.add_column("Filename")
    table.add_column("Enabled")

    for component in components:
        table.add_row(
            component.library_name, component.filename, component.enabled.__str__()
        )

    console = Console()
    console.print(table)
