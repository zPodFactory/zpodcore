from typing import List

import typer
from rich import print
from rich.table import Table
from typing_extensions import Annotated

from zpodcli.cmd import zpod_component_cli, zpod_dns_cli, zpod_permission_cli
from zpodcli.lib.utils import console_print
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler
from zpodsdk.models.endpoint_view_full import EndpointViewFull
from zpodsdk.models.zpod_create import ZpodCreate
from zpodsdk.models.zpod_permission import ZpodPermission
from zpodsdk.models.zpod_view import ZpodView

app = typer.Typer(help="Manage zPods")
app.add_typer(zpod_component_cli.app, name="component")
app.add_typer(zpod_dns_cli.app, name="dns")
app.add_typer(zpod_permission_cli.app, name="permission")


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


def generate_table(zpods: list[ZpodView]):
    title = "zPod List"
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

    for zpod in sorted(zpods, key=lambda x: x.name):
        counts = {}
        for component in zpod.components:
            component_name = component.component.component_name
            counts.setdefault(component_name, 0)
            counts[component_name] += 1

        components = "".join(
            f"{value} x [yellow3]{key}[/yellow3]\n" for key, value in counts.items()
        )
        networks = "".join(
            f" - [cornflower_blue]{network.cidr}[/cornflower_blue]\n"
            for network in zpod.networks
        )

        owners = ""
        for zpod_perm in zpod.permissions:
            if zpod_perm.permission == ZpodPermission.OWNER:
                owners = "\n".join(sorted(x.username for x in zpod_perm.users))

        table.add_row(
            f"[bold]{zpod.name}[/bold]",
            f"[sky_blue2]{zpod.domain}[/sky_blue2]",
            f"[tan]{zpod.profile}[/tan]",
            components,
            f"[dark_khaki]{zpod.endpoint.name}[/dark_khaki]",
            networks,
            f"[light_pink1]{owners}[/light_pink1]",
            zpod.password,
            get_status_markdown(zpod.status),
        )

    console_print(title, table)


@app.command(name="list")
@unexpected_status_handler
def zpod_list(
    *,
    owner: Annotated[
        str,
        typer.Option(
            "--owner",
            "-o",
            help="filter by owner",
            show_default=False,
        ),
    ] = "",
):
    """
    List zPods
    """
    print("Listing zPods")

    z: ZpodClient = ZpodClient()
    zpods = z.zpods_get_all.sync()

    if not owner:
        # If no owner filter is specified, show all zPods
        filtered_zpods = zpods
    else:
        # Filter zPods by owner
        filtered_zpods = []
        for zpod in zpods:
            # Check if the specified owner is an owner of this zPod
            owner_permissions = [
                perm
                for perm in zpod.permissions
                if perm.permission == ZpodPermission.OWNER
                and any(owner == user.username for user in perm.users)
            ]
            if owner_permissions:
                filtered_zpods.append(zpod)

    generate_table(filtered_zpods)


@app.command(name="destroy", no_args_is_help=True)
@unexpected_status_handler
def zpod_destroy(
    zpod_names: Annotated[
        List[str],
        typer.Argument(
            help="zPod Name",
            show_default=False,
        ),
    ],
):
    """
    Destroy a zPod
    """
    z: ZpodClient = ZpodClient()

    for zpod_name in zpod_names:
        z.zpods_delete.sync(id=f"name={zpod_name}")
        print(
            f"zPod [magenta]{zpod_name}[/magenta] has been scheduled for destruction."
        )


@app.command(name="create", no_args_is_help=True)
@unexpected_status_handler
def zpod_create(
    *,
    zpod_name: Annotated[
        str,
        typer.Argument(
            help="zPod name",
            show_default=False,
        ),
    ],
    description: Annotated[
        str,
        typer.Option(
            "--description",
            help="Description",
            show_default=False,
        ),
    ] = "",
    domain: Annotated[
        str,
        typer.Option(
            "--domain",
            help="Domain override",
            show_default=False,
        ),
    ] = "",
    endpoint: Annotated[
        str,
        typer.Option(
            "--endpoint",
            "-e",
            help="Endpoint to deploy zPod",
            show_default=False,
        ),
    ] = None,
    profile: Annotated[
        str,
        typer.Option(
            "--profile",
            "-p",
            help="Profile definition",
            show_default=False,
        ),
    ] = None,
    enet_name: Annotated[
        str,
        typer.Option(
            "--enet",
            help="Enet override",
            show_default=False,
        ),
    ] = None,
):
    """
    Create a zPod
    """
    z: ZpodClient = ZpodClient()

    # If no endpoint specified, try to find the only available one
    if endpoint is None:
        endpoints = z.endpoints_get_all.sync()
        if len(endpoints) == 1:
            endpoint = endpoints[0].name
            print(f"Using default endpoint: [magenta]{endpoint}[/magenta]")
        else:
            print("Error: No endpoint specified and multiple endpoints are available.")
            print("Please specify an endpoint using the --endpoint (-e) option.")
            print("\nAvailable endpoints:")
            for ep in endpoints:
                print(f"  - {ep.name}")
            raise typer.Exit(1)

    # If no profile specified, try to get the default profile from settings
    if profile is None:
        settings = z.settings_get_all.sync()
        default_profile = None
        for setting in settings:
            if setting.name == "ff_zpod_default_profile":
                default_profile = setting.value
                break

        if default_profile:
            profile = default_profile
            print(f"Using default profile: [magenta]{profile}[/magenta]")
        else:
            print(
                "Error: No profile specified and no default profile found in settings `ff_zpod_default_profile`."
            )
            print("Please specify a profile using the --profile (-p) option.")
            raise typer.Exit(1)

    ep: EndpointViewFull = z.endpoints_get.sync(id=f"name={endpoint}")
    zpod_details = ZpodCreate(
        name=zpod_name,
        domain=domain,
        description=description,
        profile=profile,
        endpoint_id=ep.id,
        enet_name=enet_name,
    )

    z.zpods_create.sync(body=zpod_details)
    print(f"zPod [magenta]{zpod_name}[/magenta] is being deployed...")
