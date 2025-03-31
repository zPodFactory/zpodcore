import time
from datetime import datetime
from typing import Annotated

import typer
from rich import print
from rich.console import Group
from rich.json import JSON
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table

from zpodcli.cmd import (
    zpod_component_cli,
    zpod_dns_cli,
    zpod_info_cli,
    zpod_permission_cli,
)
from zpodcli.lib.utils import console_print, get_status_markdown
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler
from zpodsdk.models.endpoint_view_full import EndpointViewFull
from zpodsdk.models.zpod_create import ZpodCreate
from zpodsdk.models.zpod_permission import ZpodPermission
from zpodsdk.models.zpod_view import ZpodView

app = typer.Typer(help="Manage zPods")
app.add_typer(zpod_component_cli.app, name="component")
app.add_typer(zpod_dns_cli.app, name="dns")
app.add_typer(zpod_info_cli.app)
app.add_typer(zpod_permission_cli.app, name="permission")


def generate_table(zpods: list[ZpodView], return_table=False):
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

    if return_table:
        return table
    else:
        console_print(title, table)


def filter_zpods_by_owner(zpods: list[ZpodView], owner: str) -> list[ZpodView]:
    """Filter zPods by owner.

    Args:
        zpods: List of zPods to filter
        owner: Owner username to filter by

    Returns:
        Filtered list of zPods owned by the specified user
    """
    if not owner:
        return zpods
    return [
        zpod
        for zpod in zpods
        if any(
            perm.permission == ZpodPermission.OWNER
            and any(owner == user.username for user in perm.users)
            for perm in zpod.permissions
        )
    ]


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
    json_: Annotated[
        bool,
        typer.Option(
            "--json",
            "-j",
            help="Display using json",
            is_flag=True,
        ),
    ] = False,
    wait: Annotated[
        bool,
        typer.Option(
            "--wait",
            "-w",
            help="Refresh list every 5 seconds (Ctrl+C to quit)",
            is_flag=True,
        ),
    ] = False,
):
    """
    List zPods
    """
    z: ZpodClient = ZpodClient()

    if wait:
        if json_:
            print("Error: Cannot use --wait (-w) with --json (-j) flags together.")
            raise typer.Exit(1)
        with Live(refresh_per_second=1, transient=False) as live:
            while True:
                zpods = z.zpods_get_all.sync()
                filtered_zpods = filter_zpods_by_owner(zpods, owner)
                table = generate_table(filtered_zpods, return_table=True)
                live.update(table)
                time.sleep(5)
    else:
        zpods = z.zpods_get_all.sync()
        filtered_zpods = filter_zpods_by_owner(zpods, owner)

        if json_:
            zpods_dict = [zpod.to_dict() for zpod in filtered_zpods]
            print(JSON.from_data(zpods_dict, sort_keys=True))
        else:
            generate_table(filtered_zpods)


@app.command(name="destroy", no_args_is_help=True)
@unexpected_status_handler
def zpod_destroy(
    zpod_names: Annotated[
        list[str],
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
    wait: Annotated[
        bool,
        typer.Option(
            "--wait",
            "-w",
            help="Wait for task to complete",
            is_flag=True,
        ),
    ] = False,
    no_spinner: Annotated[
        bool,
        typer.Option(
            "--no-spinner",
            help="Disable spinner animation when waiting",
            is_flag=True,
        ),
    ] = False,
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

    # Get profile information once before creating the zpod
    profile_info = z.profiles_get.sync(id=f"name={profile}")
    # Extract component order from profile structure
    component_order = []
    for component in profile_info.profile:
        if isinstance(component, list):
            # Handle ESXi components
            for esxi in component:
                component_order.append((esxi.component_uid, esxi.hostname))
        else:
            # Handle single components like zbox
            component_order.append(component.component_uid)

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

    if wait:
        try:
            if no_spinner:
                while True:
                    zpod = z.zpods_get.sync(id=f"name={zpod_name}")
                    status = zpod.status

                    if status == "ACTIVE":
                        print(
                            f"zPod [magenta]{zpod_name}[/magenta] deployment [green]success[/green]!"
                        )
                        break
                    elif status in ["DEPLOY_FAILED", "DESTROY_FAILED"]:
                        print(
                            f"\nzPod [magenta]{zpod_name}[/magenta] deployment [red]failure[/red]!"
                        )
                        raise typer.Exit(1)

                    time.sleep(5)
            else:
                with Live(
                    refresh_per_second=10,
                    transient=False,
                    auto_refresh=True,
                ) as live:
                    # Store start time for elapsed time calculation
                    start_time = datetime.now()
                    while True:
                        # Calculate elapsed time
                        elapsed = datetime.now() - start_time
                        hours = elapsed.seconds // 3600
                        minutes = (elapsed.seconds % 3600) // 60
                        seconds = elapsed.seconds % 60
                        elapsed_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                        zpod_status_table = Table(
                            show_header=False,
                            box=None,
                            padding=(0, 0),
                        )
                        zpod_status_table.add_column("Status", style="bold")
                        zpod_status_table.add_column("Spinner", style="yellow")

                        # Only check status every 5 seconds
                        if elapsed.seconds % 5 == 0:
                            zpod = z.zpods_get.sync(id=f"name={zpod_name}")
                            status = zpod.status

                            # Create component status lines
                            component_status_table = Table(
                                show_header=False,
                                box=None,
                                padding=(0, 0),
                            )
                            component_status_table.add_column("Status", style="bold")
                            component_status_table.add_column("Spinner", style="yellow")

                            # Update component statuses
                            for component_info in component_order:
                                if isinstance(component_info, tuple):
                                    component_uid, hostname = component_info
                                else:
                                    component_uid = component_info
                                    hostname = None

                                component = next(
                                    (
                                        c
                                        for c in zpod.components
                                        if c.component.component_uid == component_uid
                                        and (hostname is None or c.hostname == hostname)
                                    ),
                                    None,
                                )
                                if component:
                                    if component.status not in [
                                        "ACTIVE",
                                        "DEPLOY_FAILED",
                                    ]:
                                        component_status_table.add_row(
                                            f"- {component.hostname}[[yellow3]{component.component.component_uid}[/yellow3]]: {get_status_markdown(component.status)} ",
                                            Spinner("dots", style="yellow"),
                                        )
                                    else:
                                        component_status_table.add_row(
                                            f"- {component.hostname}[[yellow3]{component.component.component_uid}[/yellow3]]: {get_status_markdown(component.status)}",
                                            "",
                                        )

                        if status not in ["ACTIVE", "DEPLOY_FAILED"]:
                            zpod_status_table.add_row(
                                f"Overall status: {get_status_markdown(status)} [dim]({elapsed_str})[/dim] ",
                                Spinner("dots", style="yellow"),
                            )
                        else:
                            zpod_status_table.add_row(
                                f"Overall status: {get_status_markdown(status)} [dim]({elapsed_str})[/dim]",
                                "",
                            )

                        # Create a group with the status table
                        layout = Group(
                            zpod_status_table,
                            component_status_table,
                        )
                        live.update(layout)

                        if status == "ACTIVE":
                            live.stop()
                            print(
                                f"zPod [magenta]{zpod_name}[/magenta] deployment [green]success[/green]!"
                            )
                            break
                        elif status == "DEPLOY_FAILED":
                            live.stop()
                            print(
                                f"\nzPod [magenta]{zpod_name}[/magenta] deployment [red]failure[/red]!"
                            )
                            raise typer.Exit(1)

                        # Update elapsed time every second
                        time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopped monitoring zPod deployment.")
            print(
                f"zPod [magenta]{zpod_name}[/magenta] is still being deployed in the background."
            )
            print(
                "You can check its status later using 'zpod list' or 'zpod info' command."
            )
