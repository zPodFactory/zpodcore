import typer
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated

from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler

app = typer.Typer(help="Manage Components")

console = Console()


def get_status_markdown(status: str):
    match status:
        case "SCHEDULED":
            return "[royal_blue1]SCHEDULED[/royal_blue1]"
        case "COMPLETED" | "ACTIVE" | "DOWNLOAD_COMPLETED":
            return f"[dark_sea_green4]{status}[/dark_sea_green4]"
        case "NOT_STARTED" | "INACTIVE":
            return f"[grey63]{status}[/grey63]"
        case _:
            try:
                if percentage := int(status):
                    return f"[deep_sky_blue1]Downloading... ({percentage}%)[/deep_sky_blue1]"  # noqa: E501
            except Exception:
                return f"[indian_red]{status}[/indian_red]"


def generate_table(components: list, component_uid: str = None, action: str = None):
    title = f"{action} {component_uid}" if len(components) == 1 else "Component List"

    table = Table(
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("UID")
    table.add_column("Name")
    table.add_column("Version")
    table.add_column("Library")
    table.add_column("Description")
    table.add_column("Status")
    table.add_column("Download Status")
    for component in components:
        table.add_row(
            f"[yellow3]{component.component_uid}[/yellow3]",
            f"[medium_purple1]{component.component_name}[/medium_purple1]",
            f"[cornflower_blue]{component.component_version}[/cornflower_blue]",
            f"[green]{component.library_name}[/green]",
            component.component_description,
            get_status_markdown(component.status),
            get_status_markdown(component.download_status),
        )
    console.print(table)


@app.command(name="list")
@unexpected_status_handler
def component_list(
    available: Annotated[
        bool,
        typer.Option("-a", help="Show all library components"),
    ] = False,
):
    """
    List Components
    """

    z: ZpodClient = ZpodClient()
    components = z.components_get_all.sync()
    # Sort component by unique uid name
    sorted_components = sorted(components, key=lambda c: c.component_uid)

    # filter only completed/available components
    filtered_components = []
    if not available:
        filtered_components.extend(c for c in sorted_components if c.status == "ACTIVE")
        sorted_components = filtered_components

    generate_table(sorted_components)


@app.command(name="enable", no_args_is_help=True)
@unexpected_status_handler
def component_enable(
    component_uid: Annotated[
        str,
        typer.Option("--uid"),
    ],
):
    """
    Enable Component
    """

    z: ZpodClient = ZpodClient()
    component = z.components_enable.sync(id=f"uid={component_uid}")
    generate_table(components=[component], component_uid=component_uid, action="Enable")


@app.command(name="get", no_args_is_help=True)
@unexpected_status_handler
def component_get(
    component_uid: Annotated[
        str,
        typer.Option("--uid"),
    ],
):
    """
    Get Specific Component Information
    """

    z: ZpodClient = ZpodClient()
    component = z.components_get.sync(id=f"uid={component_uid}")

    generate_table(components=[component], component_uid=component_uid, action="Get")


@app.command(name="disable", no_args_is_help=True)
@unexpected_status_handler
def component_disable(
    component_uid: Annotated[
        str,
        typer.Option("--uid"),
    ],
):
    """
    Disable Specific Component
    """

    z: ZpodClient = ZpodClient()
    component = z.components_disable.sync(id=f"uid={component_uid}")
    generate_table(
        components=[component], component_uid=component_uid, action="Disable"
    )
