import json
from typing import List

import typer
from rich import print
from rich.console import Console
from rich.table import Table
from zpod.models.endpoint_view_full import EndpointViewFull
from zpod.models.instance_create import InstanceCreate
from zpod.models.instance_permission import InstancePermission
from zpod.models.instance_view import InstanceView

from zpodcli.cmd import instance_component
from zpodcli.lib import utils, zpod_client

app = typer.Typer(help="Manage zPods Instances")
app.add_typer(instance_component.app, name="component")

console = Console()


def get_status_markdown(status: str):
    match status:
        case "ACTIVE":
            return f"[dark_sea_green4]{status}[/dark_sea_green4]"
        case "PENDING" | "BUILDING":
            return f"[grey63]{status}...[/grey63]"
        case "DELETING":
            return f"[orange3]{status}...[/orange3]"
        case "DELETED":
            return f"[dark_orange3]{status}[/dark_orange3]"
        case "DEPLOY_FAILED" | "DESTROY_FAILED":
            return f"[indian_red]{status}[/indian_red]"
        case _:
            return "[royal_blue1]UNKNOWN[/royal_blue1]"


def generate_table(instances: list[InstanceView], action: str = None):
    title = f"{action} Instances"

    table = Table(
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Name")
    table.add_column("Domain")
    table.add_column("Profile")
    table.add_column("Components")
    table.add_column("Endpoint")
    table.add_column("Networks")
    table.add_column("Owner")
    table.add_column("Password")
    table.add_column("Status")

    for instance in instances:
        counts = {}

        for component in instance.components:
            component_name = component.component.component_name
            if component_name in counts:
                counts[component_name] += 1
            else:
                counts[component_name] = 1

        components = "".join(
            f"{value} x [yellow3]{key}[/yellow3]\n" for key, value in counts.items()
        )
        networks = ""
        networks = "".join(
            f" - [cornflower_blue]{network.cidr}[/cornflower_blue]\n"
            for network in instance.networks
        )

        owner = ""
        for instance_permission in instance.permissions:
            if instance_permission.permission == InstancePermission.INSTANCE_OWNER:
                owner = instance_permission.users[0].username

        table.add_row(
            f"[bold]{instance.name}[/bold]",
            f"[plum4]{instance.domain}[/plum4]",
            f"[tan]{instance.profile}[/tan]",
            components,
            f"[dark_khaki]{instance.endpoint.name}[/dark_khaki]",
            networks,
            owner,
            instance.password,
            get_status_markdown(instance.status),
        )

    console.print(table)


@app.command(name="list")
def instance_list():
    """
    List zPods
    """
    print("Listing zPods")

    z = zpod_client.ZpodClient()
    instances = z.instances_get_all.sync()
    generate_table(instances, "List")


@app.command(name="delete", no_args_is_help=True)
def instance_delete(
    names: List[str] = typer.Option(..., "--name", "-n"),
):
    """
    Delete a zPod
    """
    z = zpod_client.ZpodClient()

    for name in names:
        instance = z.instances_delete.sync_detailed(id=f"name={name}")
        if instance.status_code == 204:
            console.print(
                f"Instance [magenta]{name}[/magenta] has been scheduled for deletion."
            )
        else:
            content = json.loads(instance.content.decode())
            error_message = content["detail"]
            console.print(f"Error: {error_message}", style="indian_red")


@app.command(name="create", no_args_is_help=True)
def instance_create(
    name: str = typer.Option(..., "--name", "-n"),
    description: str = typer.Option("", "--description"),
    domain: str = typer.Option("", "--domain"),
    endpoint: str = typer.Option(..., "--endpoint", "-e"),
    profile: str = typer.Option(..., "--profile", "-p"),
    enet_name: str = typer.Option(None, "--enet"),
):
    """
    Create a zPod
    """
    z = zpod_client.ZpodClient()

    endpoints: list[EndpointViewFull] = z.endpoints_get_all.sync()
    if endpoints is None:
        print("There is no endpoints available for deployment")

    ep_id = None
    for ep in endpoints:
        if ep.name == endpoint:
            ep_id = ep.id

    instance_details = InstanceCreate(
        name=name,
        domain=domain,
        description=description,
        profile=profile,
        endpoint_id=ep_id,
        enet_name=enet_name,
    )

    result = z.instances_create.sync_detailed(json_body=instance_details)
    if result.status_code == 201:
        print(f"Instance [magenta]{name}[/magenta] is being deployed...")
    else:
        utils.handle_response(result)
