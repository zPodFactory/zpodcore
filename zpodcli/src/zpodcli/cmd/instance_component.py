from typing import List

import typer
from rich import print
from rich.console import Console
from rich.table import Table
from zpod.models.instance_component_create import InstanceComponentCreate
from zpod.models.instance_component_view import InstanceComponentView
from zpod.models.instance_view import InstanceView

from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler

app = typer.Typer(help="Manage zPods Instance components", no_args_is_help=True)

console = Console()


def generate_table(
    instance: InstanceView, instance_components: list[InstanceComponentView]
):
    title = f"{instance.name} Component List"

    table = Table(
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Component UID")
    table.add_column("Name")
    table.add_column("Version")
    table.add_column("Description")
    table.add_column("FQDN")

    for ic in instance_components:
        table.add_row(
            f"[yellow3]{ic.component.component_uid}[/yellow3]",
            f"[light_coral]{ic.component.component_name}[/light_coral]",
            f"[cornflower_blue]{ic.component.component_version}[/cornflower_blue]",
            ic.component.component_description,
            f"[sky_blue2]https://{ic.fqdn}[/sky_blue2]",
        )

    console.print(table)


@app.command(name="list", no_args_is_help=True)
@unexpected_status_handler
def instance_component_list(
    instance_name: str = typer.Option(..., "-i", help="instance name"),
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
    instance_name: str = typer.Option(..., "-i", help="instance name"),
    component_uid: str = typer.Option(..., "-c", help="component uid"),
    host_id: int = typer.Option(None, "--host_id", help="host id"),
    hostname: str = typer.Option(None, "--hostname", help="hostname"),
    vcpu: int = typer.Option(None, "--vcpu", help="vcpu"),
    vmem: int = typer.Option(None, "--vmem", help="vmem"),
):
    """
    Adding component to instance
    """
    print(f"Adding component {component_uid} to instance {instance_name}")

    z: ZpodClient = ZpodClient()
    instance = z.instances_get.sync(id=f"name={instance_name}")

    z.instances_components_add.sync(
        instance.id,
        json_body=InstanceComponentCreate(
            component_uid=component_uid,
            host_id=host_id,
            hostname=hostname,
            vcpu=vcpu,
            vmem=vmem,
        ),
    )


if __name__ == "__main__":
    app()
