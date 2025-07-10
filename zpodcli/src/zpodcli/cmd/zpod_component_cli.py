import time
from typing import Annotated

import typer
from rich import print
from rich.live import Live
from rich.table import Table

from zpodcli.lib.prompt import confirm
from zpodcli.lib.utils import console_print, get_status_markdown, json_print
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler
from zpodsdk.models.zpod_component_create import ZpodComponentCreate
from zpodsdk.models.zpod_component_view import ZpodComponentView

app = typer.Typer(help="Manage zPod Components", no_args_is_help=True)


def generate_table(
    zpod_components: list[ZpodComponentView],
    return_table=False,
):
    title = "zPod Component List"

    table = Table(
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Hostname")
    table.add_column("Component UID")
    table.add_column("FQDN")
    table.add_column("[light_pink1]SSH[/light_pink1]/[dark_khaki]UI[/dark_khaki] users")
    table.add_column("Description")
    table.add_column("Status")

    for zc in zpod_components:
        usernames_list = []
        for username in zc.usernames:
            if username["type"] == "ssh":
                usernames_list.append(
                    f"[light_pink1]{username['username']}[/light_pink1]"
                )
            elif username["type"] == "ui":
                usernames_list.append(
                    f"[dark_khaki]{username['username']}[/dark_khaki]"
                )

        # On joint les noms d'utilisateur s'il y en a, sinon chaîne vide
        usernames = ", ".join(usernames_list)

        table.add_row(
            f"[sky_blue2]{zc.hostname}[/sky_blue2]",
            f"[yellow3]{zc.component.component_uid}[/yellow3]",
            f"[sky_blue2]https://{zc.fqdn}[/sky_blue2]",
            usernames,
            zc.component.component_description,
            get_status_markdown(zc.status),
        )

    if return_table:
        return table

    console_print(title, table)

    # Display password if it exists in the first component
    if zpod_components and zpod_components[0].password:
        print(f"\nzPod password: [red]{zpod_components[0].password}[/red]")


def sort_components_by_ip(
    components: list[ZpodComponentView],
) -> list[ZpodComponentView]:
    """Sort components by IP address in ascending order.

    Args:
        components: List of components to sort

    Returns:
        Sorted list of components, with components without IPs at the beginning
    """
    return sorted(
        components,
        key=lambda zc: [int(i) for i in zc.ip.split(".")] if zc.ip else [0, 0, 0, 0],
    )


@app.command(name="list", no_args_is_help=True)
@unexpected_status_handler
def zpod_component_list(
    zpod_name: Annotated[
        str,
        typer.Argument(
            help="zPod name",
            show_default=False,
        ),
    ],
    json_: Annotated[
        bool,
        typer.Option(
            "--json",
            "-j",
            help="Display using json",
            is_flag=True,
        ),
    ] = False,
    no_color: Annotated[
        bool,
        typer.Option(
            "--no-color",
            help="Disable color output",
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
    List zPod Components
    """
    if wait:
        if json_:
            print("Error: Cannot use --wait (-w) with --json (-j) flags together.")
            raise typer.Exit(1)
        with Live(refresh_per_second=1, transient=False) as live:
            while True:
                z: ZpodClient = ZpodClient()
                zpod_components: list[ZpodComponentView] = (
                    z.zpods_components_get_all.sync(id=f"name={zpod_name}")
                )

                sorted_zpod_components = sort_components_by_ip(zpod_components)
                table = generate_table(sorted_zpod_components, return_table=True)
                live.update(table)
                time.sleep(5)
    else:
        z: ZpodClient = ZpodClient()
        zpod_components: list[ZpodComponentView] = z.zpods_components_get_all.sync(
            id=f"name={zpod_name}"
        )

        sorted_zpod_components = sort_components_by_ip(zpod_components)

        if json_:
            zpod_components_dict = [
                component.to_dict() for component in sorted_zpod_components
            ]
            json_print(zpod_components_dict, no_color=no_color)
        else:
            generate_table(sorted_zpod_components)


@app.command(name="add", no_args_is_help=True)
@unexpected_status_handler
def zpod_component_add(
    zpod_name: Annotated[
        str,
        typer.Argument(
            help="zPod name",
            show_default=False,
        ),
    ],
    component_uid: Annotated[
        str,
        typer.Option(
            "--component-uid",
            "-c",
            help="Component uid",
            show_default=False,
        ),
    ],
    host_id: Annotated[
        int,
        typer.Option(
            "--host-id",
            help="Host id",
            show_default=False,
        ),
    ] = None,
    hostname: Annotated[
        str,
        typer.Option(
            "--hostname",
            help="Hostname",
            show_default=False,
        ),
    ] = None,
    vcpu: Annotated[
        int,
        typer.Option(
            "--vcpu",
            help="vcpu",
            show_default=False,
        ),
    ] = None,
    vmem: Annotated[
        int,
        typer.Option(
            "--vmem",
            help="vmem",
            show_default=False,
        ),
    ] = None,
    vdisks: Annotated[
        list[int],
        typer.Option(
            "--vdisks",
            help="vdisks",
            show_default=False,
        ),
    ] = None,
):
    """
    Add Component to zPod
    """
    print(f"Adding component {component_uid} to zPod {zpod_name}")

    z: ZpodClient = ZpodClient()
    z.zpods_components_add.sync(
        id=f"name={zpod_name}",
        body=ZpodComponentCreate(
            component_uid=component_uid,
            host_id=host_id,
            hostname=hostname,
            vcpu=vcpu,
            vmem=vmem,
            vdisks=vdisks,
        ),
    )


@app.command(name="remove", no_args_is_help=True)
@unexpected_status_handler
def zpod_component_remove(
    zpod_name: Annotated[
        str,
        typer.Argument(
            help="zPod name",
            show_default=False,
        ),
    ],
    hostname: Annotated[
        str,
        typer.Option(
            "-h",
            "--hostname",
            help="Hostname",
            show_default=False,
        ),
    ],
    yes: Annotated[
        bool,
        typer.Option(
            "-y",
            "--yes",
            help="Automatic yes to prompts.",
            show_default=False,
        ),
    ] = False,
):
    """
    Remove Component from zPod
    """
    if not yes:
        confirm(
            f"Are you sure you want to remove component [magenta]{hostname}[/magenta] "
            f"from [magenta]{zpod_name}[/magenta]?",
        )

    print(
        f"Removing component [magenta]{hostname}[/magenta] "
        f"from zPod [magenta]{zpod_name}[/magenta]"
    )

    z: ZpodClient = ZpodClient()
    z.zpods_components_remove.sync(
        id=f"name={zpod_name}",
        component_id=f"hostname={hostname}",
    )


if __name__ == "__main__":
    app()
