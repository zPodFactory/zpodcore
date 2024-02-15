from typing import List

import typer
from rich import print
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated
from zpod.models.instance_component_create import InstanceComponentCreate
from zpod.models.instance_component_view import InstanceComponentView
from zpod.models.instance_view import InstanceView

from zpodcli.lib.utils import confirm
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler

app = typer.Typer(help="Manage zPod Instance Components", no_args_is_help=True)

console = Console()


def get_status_markdown(status: str):
    match status:
        case "ACTIVE":
            return f"[dark_sea_green4]{status}[/dark_sea_green4]"
        case "BUILDING":
            return f"[grey63]{status}...[/grey63]"
        case "ADD_FAILED" | "DELETE_FAILED":
            return f"[indian_red]{status}[/indian_red]"
        case _:
            return "[royal_blue1]UNKNOWN[/royal_blue1]"


def generate_table(
    instance: InstanceView,
    instance_components: list[InstanceComponentView],
):
    title = f"{instance.name} Component List"

    table = Table(
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Hostname")
    table.add_column("FQDN")
    table.add_column("Status")
    table.add_column("Component UID")
    table.add_column("Name")
    table.add_column("Version")
    table.add_column("Description")

    for ic in instance_components:
        table.add_row(
            f"[sky_blue2]{ic.hostname}[/sky_blue2]",
            f"[sky_blue2]https://{ic.fqdn}[/sky_blue2]",
            get_status_markdown(ic.status),
            f"[yellow3]{ic.component.component_uid}[/yellow3]",
            f"[light_coral]{ic.component.component_name}[/light_coral]",
            f"[cornflower_blue]{ic.component.component_version}[/cornflower_blue]",
            ic.component.component_description,
        )

    console.print(table)


@app.command(name="list", no_args_is_help=True)
@unexpected_status_handler
def instance_component_list(
    instance_name: Annotated[
        str,
        typer.Option("-i", help="instance name"),
    ],
):
    """
    List instance components
    """
    print(f"Listing {instance_name} components")

    z: ZpodClient = ZpodClient()
    instance = z.instances_get.sync(id=f"name={instance_name}")

    if instance.name == instance_name:
        instance_components: List[
            InstanceComponentView
        ] = z.instances_components_get_all.sync(instance.id)

        # Sort per FQDN
        sorted_instance_components = sorted(instance_components, key=lambda ic: ic.fqdn)

        generate_table(instance, sorted_instance_components)


@app.command(name="add", no_args_is_help=True)
@unexpected_status_handler
def instance_component_add(
    instance_name: Annotated[
        str,
        typer.Option("-i", help="instance name"),
    ],
    component_uid: Annotated[
        str,
        typer.Option("-c", help="component uid"),
    ],
    host_id: Annotated[
        int,
        typer.Option("--host_id", help="host id"),
    ] = None,
    hostname: Annotated[
        str,
        typer.Option("--hostname", help="hostname"),
    ] = None,
    vcpu: Annotated[
        int,
        typer.Option("--vcpu", help="vcpu"),
    ] = None,
    vmem: Annotated[
        int,
        typer.Option("--vmem", help="vmem"),
    ] = None,
):
    """
    Add component to instance
    """
    print(f"Adding component {component_uid} to instance {instance_name}")

    z: ZpodClient = ZpodClient()
    instance = z.instances_get.sync(id=f"name={instance_name}")

    z.instances_components_add.sync(
        instance.id,
        body=InstanceComponentCreate(
            component_uid=component_uid,
            host_id=host_id,
            hostname=hostname,
            vcpu=vcpu,
            vmem=vmem,
        ),
    )


@app.command(name="remove", no_args_is_help=True)
@unexpected_status_handler
def instance_component_remove(
    instance_name: Annotated[
        str,
        typer.Option("-i", "--instance", help="instance name"),
    ],
    hostname: Annotated[
        str,
        typer.Option("-h", "--hostname", help="hostname"),
    ],
    yes: Annotated[
        bool,
        typer.Option("-y", "--yes", help="Automatic yes to prompts."),
    ] = False,
):
    """
    Remove component from instance
    """
    if not yes:
        confirm(
            f"Are you sure you want to remove component [magenta]{hostname}[/magenta] "
            f"from [magenta]{instance_name}[/magenta]?",
        )

    print(
        f"Removing component [magenta]{hostname}[/magenta] "
        f"from instance [magenta]{instance_name}[/magenta]"
    )

    z: ZpodClient = ZpodClient()
    z.instances_components_remove.sync(
        id=f"name={instance_name}",
        component_id=f"hostname={hostname}",
    )


if __name__ == "__main__":
    app()
