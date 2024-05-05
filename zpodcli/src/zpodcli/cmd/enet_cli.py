import typer
from rich import print
from rich.table import Table
from typing_extensions import Annotated

from zpodcli.lib.utils import console_print
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler
from zpodsdk.models.endpoint_enet_create import EndpointENetCreate
from zpodsdk.models.endpoint_view_full import EndpointViewFull

app = typer.Typer(help="Manage ENets")


def generate_table(enets: list):
    title = "ENet List"
    table = Table(
        "ENet Name",
        "Project Id",
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    for enet in enets:
        table.add_row(enet.name, enet.project_id)

    console_print(title, table)


@app.command(name="list", no_args_is_help=True)
@unexpected_status_handler
def enet_list(
    endpoint_name: Annotated[
        str,
        typer.Argument(
            help="Endpoint name",
            show_default=False,
        ),
    ],
):
    """
    List ENets
    """
    z = ZpodClient()

    ep: EndpointViewFull = z.endpoints_get.sync(id=f"name={endpoint_name}")
    enets = z.endpoints_enet_get_all.sync(id=ep.id)
    generate_table(enets)


@app.command(name="create", no_args_is_help=True)
@unexpected_status_handler
def enet_create(
    endpoint_name: Annotated[
        str,
        typer.Argument(
            help="Endpoint name",
            show_default=False,
        ),
    ],
    enet_name: Annotated[
        str,
        typer.Argument(
            help="ENet name",
            show_default=False,
        ),
    ],
):
    """
    Create ENet
    """
    z = ZpodClient()

    ep: EndpointViewFull = z.endpoints_get.sync(id=f"name={endpoint_name}")
    z.endpoints_enet_create.sync(id=ep.id, body=EndpointENetCreate(name=enet_name))
    print(f"ENet [magenta]{enet_name}[/magenta] has been created.")


@app.command(name="delete", no_args_is_help=True)
@unexpected_status_handler
def enet_delete(
    endpoint_name: Annotated[
        str,
        typer.Argument(
            help="Endpoint name",
            show_default=False,
        ),
    ],
    enet_name: Annotated[
        str,
        typer.Argument(
            help="ENet name",
            show_default=False,
        ),
    ],
):
    """
    Delete ENet
    """
    z = ZpodClient()

    ep: EndpointViewFull = z.endpoints_get.sync(id=f"name={endpoint_name}")
    z.endpoints_enet_delete.sync(id=ep.id, name=enet_name)
    print(f"ENet [magenta]{enet_name}[/magenta] has been scheduled for deletion.")
