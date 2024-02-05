import typer
from rich import print
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated
from zpod.models.endpoint_enet_create import EndpointENetCreate
from zpod.models.endpoint_view_full import EndpointViewFull

from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler

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


@app.command(name="list", no_args_is_help=True)
@unexpected_status_handler
def enet_list(
    endpoint: Annotated[
        str,
        typer.Option("--endpoint", "-e"),
    ],
):
    """
    List ENets
    """
    z = ZpodClient()

    ep: EndpointViewFull = z.endpoints_get.sync(id=f"name={endpoint}")
    enets = z.endpoints_enet_get_all.sync(id=ep.id)
    generate_table(enets, "List")


@app.command(name="create", no_args_is_help=True)
@unexpected_status_handler
def enet_create(
    endpoint: Annotated[
        str,
        typer.Option("--endpoint", "-e"),
    ],
    name: Annotated[
        str,
        typer.Option("--name", "-n"),
    ],
):
    """
    Create ENet
    """
    z = ZpodClient()

    ep: EndpointViewFull = z.endpoints_get.sync(id=f"name={endpoint}")
    z.endpoints_enet_create.sync(id=ep.id, body=EndpointENetCreate(name=name))
    print(f"ENet [magenta]{name}[/magenta] has been created.")


@app.command(name="delete", no_args_is_help=True)
@unexpected_status_handler
def enet_delete(
    endpoint: Annotated[
        str,
        typer.Option("--endpoint", "-e"),
    ],
    name: Annotated[
        str,
        typer.Option("--name", "-n"),
    ],
):
    """
    Delete ENet
    """
    z = ZpodClient()

    ep: EndpointViewFull = z.endpoints_get.sync(id=f"name={endpoint}")
    z.endpoints_enet_delete.sync(id=ep.id, name=name)
    print(f"ENet [magenta]{name}[/magenta] has been scheduled for deletion.")
