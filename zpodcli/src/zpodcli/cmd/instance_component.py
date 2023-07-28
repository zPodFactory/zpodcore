import json
from typing import List

import typer
from rich import print
from rich.console import Console
from rich.table import Table
from zpod.models.instance_component_create import InstanceComponentCreate
from zpod.models.instance_component_data_create import InstanceComponentDataCreate
from zpod.models.instance_component_data_view import InstanceComponentDataView
from zpod.models.instance_component_view import InstanceComponentView
from zpod.models.instance_view import InstanceView

from zpodcli.lib import utils, zpod_client

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

    # FIXME: for FQDN we will use the TO BE IMPLEMENTED fqdn/ipaddress on instance_components
    # instance_component.fqdn
    # instance_component.ipaddress

    for ic in instance_components:
        table.add_row(
            f"[yellow3]{ic.component.component_uid}[/yellow3]",
            f"[light_coral]{ic.component.component_name}[/light_coral]",
            f"[cornflower_blue]{ic.component.component_version}[/cornflower_blue]",
            ic.component.component_description,
            f"[sky_blue2]https://{ic.component.component_name}.{instance.domain}[/sky_blue2]",
        )

    console.print(table)


@app.command(name="list", no_args_is_help=True)
def instance_component_list(
    instance_name: str = typer.Option(..., "-i", help="instance name"),
):
    """
    List instance components
    """
    print(f"Listing {instance_name} components")

    z = zpod_client.ZpodClient()
    instances = z.instances_get_all.sync()
    for i in instances:
        if i.name == instance_name:
            instance_components: List[
                InstanceComponentView
            ] = z.instances_components_get_all.sync(i.id)

            generate_table(i, instance_components)


@app.command(name="add", no_args_is_help=True)
def instance_component_add(
    instance_name: str = typer.Option(..., "-i", help="instance name"),
    component_uid: str = typer.Option(..., "-c", help="component uid"),
):
    """
    Adding component to instance
    """
    print(f"Adding component {component_uid} to instance {instance_name}")

    z = zpod_client.ZpodClient()

    instances = z.instances_get_all.sync()
    for i in instances:
        if i.name == instance_name:
            print(f"Instance {instance_name}: Deploying component {component_uid}...")
            ic_data_create = InstanceComponentDataCreate()
            # TODO: maybe one day we will have hostname/ip/vcpu/mem/etc support here for Data
            # This will require dynamic DNS management for components, which we do not have yet.
            ic_create = InstanceComponentCreate(
                component_uid=component_uid, data=ic_data_create
            )

            z.instances_components_add.sync_detailed(i.id, json_body=ic_create)


if __name__ == "__main__":
    app()
