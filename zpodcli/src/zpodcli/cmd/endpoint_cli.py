import typer
from rich.console import Console
from rich.json import JSON
from rich.table import Table

from zpodcli.cmd import endpoint_permission_cli
from zpodcli.lib.utils import get_boolean_markdown
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler

app = typer.Typer(help="Manage Endpoints")
app.add_typer(endpoint_permission_cli.app, name="permission")


console = Console()


def generate_table(endpoints: list, action: str = None):
    title = f"{action} Endpoints"

    table = Table(
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Compute")
    table.add_column("Network")
    table.add_column("Enabled")

    for endpoint in endpoints:
        ep = endpoint.endpoints
        epc = ep.compute
        epn = ep.network

        table.add_row(
            f"[dark_khaki]{endpoint.name}[/dark_khaki]",
            endpoint.description,
            JSON.from_data(epc.to_dict()),
            JSON.from_data(epn.to_dict()),
            get_boolean_markdown(endpoint.enabled),
        )
    console.print(table)


@app.command(name="list")
@unexpected_status_handler
def endpoint_list():
    """
    List Endpoints
    """
    z = ZpodClient()
    endpoints = z.endpoints_get_all.sync()
    generate_table(endpoints, "List")
