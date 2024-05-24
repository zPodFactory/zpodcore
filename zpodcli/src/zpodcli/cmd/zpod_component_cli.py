from typing import List

import typer
from rich import print
from rich.table import Table
from typing_extensions import Annotated

from zpodcli.lib.prompt import confirm
from zpodcli.lib.utils import console_print
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler
from zpodsdk.models.zpod_component_create import ZpodComponentCreate
from zpodsdk.models.zpod_component_view import ZpodComponentView

app = typer.Typer(help="Manage zPod Components", no_args_is_help=True)


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
    zpod_components: list[ZpodComponentView],
):
    title = "zPod Component List"

    table = Table(
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Hostname")
    table.add_column("FQDN")
    table.add_column("Component UID")
    table.add_column("Name")
    table.add_column("Version")
    table.add_column("Description")
    table.add_column("Status")

    for zc in zpod_components:
        table.add_row(
            f"[sky_blue2]{zc.hostname}[/sky_blue2]",
            f"[sky_blue2]https://{zc.fqdn}[/sky_blue2]",
            f"[yellow3]{zc.component.component_uid}[/yellow3]",
            f"[light_coral]{zc.component.component_name}[/light_coral]",
            f"[cornflower_blue]{zc.component.component_version}[/cornflower_blue]",
            zc.component.component_description,
            get_status_markdown(zc.status),
        )

    console_print(title, table)


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
):
    """
    List zPod Components
    """
    print(f"Listing {zpod_name} components")
    z: ZpodClient = ZpodClient()
    zpod_components: List[ZpodComponentView] = z.zpods_components_get_all.sync(
        id=f"name={zpod_name}"
    )

    # Sort per FQDN
    sorted_zpod_components = sorted(zpod_components, key=lambda zc: zc.fqdn)
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
