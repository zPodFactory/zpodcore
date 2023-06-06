import typer
from rich.console import Console
from rich.pretty import Pretty
from rich.table import Table

from zpodcli.lib import zpod_client

app = typer.Typer(help="Manage endpoints")


console = Console()


def generate_table(endpoints: list, action: str = None):
    title = f"{action} Endpoints"

    table = Table(
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Id")
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Compute")
    table.add_column("Network")

    for endpoint in endpoints:
        ep = endpoint.endpoints
        epc = ep.compute
        epn = ep.network

        table.add_row(
            endpoint.id,
            endpoint.name,
            endpoint.description,
            Pretty(epc),
            Pretty(epn),
            f"{endpoint.enabled.__str__()}",
        )
    console.print(table)


@app.command()
def list():
    """
    List Endpoints
    """
    z = zpod_client.ZpodClient()
    endpoints = z.endpoints_get_all.sync()
    generate_table(endpoints, "List")
