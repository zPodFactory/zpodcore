import json
from typing import Optional

import typer
from rich import print
from rich.console import Console
from rich.table import Table
from zpod.models.setting_update import SettingUpdate

from zpodcli.lib import zpod_client

app = typer.Typer(help="Manage Settings")

console = Console()


def generate_table(settings: list, action: str = None):
    title = f"{action} Library"

    table = Table(
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Value")
    for setting in settings:
        table.add_row(
            f"[tan]{setting.name}[/tan]",
            f"{setting.description}",
            f"[dark_khaki]{setting.value}[/dark_khaki]",
        )
    console.print(table)


@app.command(name="list")
def setting_list():
    """
    List Settings
    """
    print("Listing Settings")

    z = zpod_client.ZpodClient()
    settings = z.settings_get_all.sync()
    generate_table(settings=settings, action="List")


@app.command(no_args_is_help=True)
def update(
    name: str = typer.Option(..., "--name", "-n"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    value: str = typer.Option(..., "--value", "-v"),
):
    """
    Update Setting
    """
    z = zpod_client.ZpodClient()
    setting = None
    if description is None:
        setting = SettingUpdate(value=value)
    else:
        setting = SettingUpdate(description=description, value=value)

    response = z.settings_update.sync_detailed(json_body=setting, id=f"name={name}")
    if response.status_code == 201:
        console.print(
            f"Setting [magenta]{name}[/magenta] has been modified to "
            f"[yellow]{value}[/yellow]."
        )
    else:
        content = json.loads(response.content.decode())
        error_message = content["detail"]
        console.print(f"Error: {error_message}", style="indian_red")
