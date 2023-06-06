import typer
from rich import print
from rich.console import Console
from rich.table import Table
from zpod.models.endpoint_enet_create import EndpointENetCreate

from zpodcli.lib import zpod_client

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
        table.add_row(
            enet.name,
            enet.project_id
        )
    console.print(table)


@app.command(no_args_is_help=True)
def list(
    endpoint: int = typer.Option(..., "--endpoint", "-e"),
):
    """
    List ENets
    """
    z = zpod_client.ZpodClient()
    enets = z.endpoints_enet_get_all.sync(id=endpoint)
    generate_table(enets, "List")


@app.command(no_args_is_help=True)
def create(
    endpoint: int = typer.Option(..., "--endpoint", "-e"),
    name: str = typer.Option(..., "--name", "-n"),
):
    """
    Create ENet
    """
    z = zpod_client.ZpodClient()
    z.endpoints_enet_create.sync(id=endpoint, json_body=EndpointENetCreate(name=name))
    print(f"ENet [magenta]{name}[/magenta] has been created.")


@app.command(no_args_is_help=True)
def delete(
    endpoint: int = typer.Option(..., "--endpoint", "-e"),
    name: str = typer.Option(..., "--name", "-n"),
):
    """
    Delete ENet
    """
    z = zpod_client.ZpodClient()
    z.endpoints_enet_delete.sync(id=endpoint, name=name)
    print(f"ENet [magenta]{name}[/magenta] has been scheduled for deletion.")
