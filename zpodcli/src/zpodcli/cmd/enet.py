import typer
from rich import print
from rich.console import Console
from rich.table import Table
from zpod.models.endpoint_view_full import EndpointViewFull
from zpod.models.endpoint_enet_create import EndpointENetCreate

from zpodcli.lib import zpod_client
from zpodcli.lib.zpod_client import ZpodClient

app = typer.Typer(help="Manage ENets")


console = Console()


def generate_table(enets: list, action: str = None):
    table = Table(
        "ENet Name",
        "Project Id",
        title=f"{action} ENets",
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    for enet in enets:
        table.add_row(enet.name, enet.project_id)
    console.print(table)

# Fetch endpoint id from name
def fetch_endpoint_id(z: ZpodClient, endpoint_name: str):

    endpoints: list[EndpointViewFull] = z.endpoints_get_all.sync()
    if endpoints is None:
        print("There is no endpoints available for deployment")

    for ep in endpoints:
        if ep.name == endpoint_name:
            return ep.id



@app.command(name="list", no_args_is_help=True)
def enet_list(
    endpoint: str = typer.Option(..., "--endpoint", "-e"),
):
    """
    List ENets
    """
    z = zpod_client.ZpodClient()

    ep_id = fetch_endpoint_id(z, endpoint)

    enets = z.endpoints_enet_get_all.sync(id=ep_id)
    generate_table(enets, "List")


@app.command(name="create", no_args_is_help=True)
def enet_create(
    endpoint: str = typer.Option(..., "--endpoint", "-e"),
    name: str = typer.Option(..., "--name", "-n"),
):
    """
    Create ENet
    """
    z = zpod_client.ZpodClient()

    ep_id = fetch_endpoint_id(z, endpoint)

    z.endpoints_enet_create.sync(id=ep_id, json_body=EndpointENetCreate(name=name))
    print(f"ENet [magenta]{name}[/magenta] has been created.")


@app.command(name="delete", no_args_is_help=True)
def enet_delete(
    endpoint: str = typer.Option(..., "--endpoint", "-e"),
    name: str = typer.Option(..., "--name", "-n"),
):
    """
    Delete ENet
    """
    z = zpod_client.ZpodClient()

    ep_id = fetch_endpoint_id(z, endpoint)

    z.endpoints_enet_delete.sync(id=ep_id, name=name)
    print(f"ENet [magenta]{name}[/magenta] has been scheduled for deletion.")
