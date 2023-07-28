import typer
from rich.console import Console
from rich.table import Table

from zpodcli.lib import zpod_client

app = typer.Typer(help="Manage components")

console = Console()


def get_status_markdown(status: str):
    match status:
        case "SCHEDULED":
            return "[royal_blue1]SCHEDULED[/royal_blue1]"
        case "COMPLETED" | "ACTIVE":
            return f"[dark_sea_green4]{status}[/dark_sea_green4]"
        case "NOT_STARTED" | "INACTIVE":
            return f"[grey63]{status}[/grey63]"
        case _:
            try:
                if percentage := int(status):
                    return f"[deep_sky_blue1]Downloading... ({percentage}%)[/deep_sky_blue1]"
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
def component_list():
    """
    List components
    """
    z = zpod_client.ZpodClient()
    components = z.components_get_all.sync()
    generate_table(components)


@app.command(name="enable", no_args_is_help=True)
def component_enable(component_uid: str = typer.Option(..., "--uid")):
    """
    Enable a component
    """
    z = zpod_client.ZpodClient()
    component = z.components_enable.sync(id=f"uid={component_uid}")
    generate_table(components=[component], component_uid=component_uid, action="Enable")


@app.command(name="get", no_args_is_help=True)
def component_get(component_uid: str = typer.Option(..., "--uid")):
    """
    Get specific component information
    """
    z = zpod_client.ZpodClient()
    component = z.components_get.sync(id=f"uid={component_uid}")

    generate_table(components=[component], component_uid=component_uid, action="Get")


@app.command(name="disable", no_args_is_help=True)
def component_disable(component_uid: str = typer.Option(..., "--uid")):
    """
    Disable specific component
    """

    z = zpod_client.ZpodClient()
    component = z.components_disable.sync(id=f"uid={component_uid}")
    generate_table(
        components=[component], component_uid=component_uid, action="Disable"
    )
