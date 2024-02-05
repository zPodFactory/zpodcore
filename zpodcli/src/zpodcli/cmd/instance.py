from typing import List

import typer
from rich import print
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated
from zpod.models.endpoint_view_full import EndpointViewFull
from zpod.models.instance_create import InstanceCreate
from zpod.models.instance_permission import InstancePermission
from zpod.models.instance_view import InstanceView

from zpodcli.cmd import instance_component, instance_permission
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler

app = typer.Typer(help="Manage zPods Instances")
app.add_typer(instance_component.app, name="component")
app.add_typer(instance_permission.app, name="permission")

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
    table.add_column("Owner(s)")
    table.add_column("Password")
    table.add_column("Status")

    for instance in sorted(instances, key=lambda x: x.name):
        counts = {}
        for component in instance.components:
            component_name = component.component.component_name
            counts.setdefault(component_name, 0)
            counts[component_name] += 1

        components = "".join(
            f"{value} x [yellow3]{key}[/yellow3]\n" for key, value in counts.items()
        )
        networks = "".join(
            f" - [cornflower_blue]{network.cidr}[/cornflower_blue]\n"
            for network in instance.networks
        )

        owners = ""
        for instance_perm in instance.permissions:
            if instance_perm.permission == InstancePermission.OWNER:
                owners = "\n".join(sorted(x.username for x in instance_perm.users))

        table.add_row(
            f"[bold]{instance.name}[/bold]",
            f"[plum4]{instance.domain}[/plum4]",
            f"[tan]{instance.profile}[/tan]",
            components,
            f"[dark_khaki]{instance.endpoint.name}[/dark_khaki]",
            networks,
            owners,
            instance.password,
            get_status_markdown(instance.status),
        )

    console.print(table)


@app.command(name="list")
@unexpected_status_handler
def instance_list():
    """
    List zPods
    """
    print("Listing zPods")

    z = ZpodClient()
    instances = z.instances_get_all.sync()
    generate_table(instances, "List")


@app.command(name="delete", no_args_is_help=True)
@unexpected_status_handler
def instance_delete(
    names: Annotated[
        List[str],
        typer.Option("--name", "-n"),
    ],
):
    """
    Delete a zPod
    """
    z = ZpodClient()

    for name in names:
        z.instances_delete.sync(id=f"name={name}")
        console.print(
            f"Instance [magenta]{name}[/magenta] has been scheduled for deletion."
        )


@app.command(name="create", no_args_is_help=True)
@unexpected_status_handler
def instance_create(
    *,
    name: Annotated[
        str,
        typer.Option("--name", "-n"),
    ],
    description: Annotated[
        str,
        typer.Option("--description"),
    ] = "",
    domain: Annotated[
        str,
        typer.Option("--domain"),
    ] = "",
    endpoint: Annotated[
        str,
        typer.Option("--endpoint", "-e"),
    ],
    profile: Annotated[
        str,
        typer.Option("--profile", "-p"),
    ],
    enet_name: Annotated[
        str,
        typer.Option("--enet"),
    ] = None,
):
    """
    Create a zPod
    """
    z = ZpodClient()

    ep: EndpointViewFull = z.endpoints_get.sync(id=f"name={endpoint}")
    instance_details = InstanceCreate(
        name=name,
        domain=domain,
        description=description,
        profile=profile,
        endpoint_id=ep.id,
        enet_name=enet_name,
    )

    z.instances_create.sync(body=instance_details)
    print(f"Instance [magenta]{name}[/magenta] is being deployed...")
