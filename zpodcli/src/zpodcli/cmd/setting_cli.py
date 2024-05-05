from typing import Optional

import typer
from rich import print
from rich.table import Table
from typing_extensions import Annotated

from zpodcli.lib.utils import console_print
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler
from zpodsdk.models.setting_update import SettingUpdate

app = typer.Typer(help="Manage Settings")


def generate_table(settings: list):
    title = "Setting List"
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
    console_print(title, table)


@app.command(name="list")
@unexpected_status_handler
def setting_list():
    """
    List Settings
    """
    z: ZpodClient = ZpodClient()
    settings = z.settings_get_all.sync()
    generate_table(settings=settings)


@app.command(no_args_is_help=True)
@unexpected_status_handler
def update(
    name: Annotated[
        str,
        typer.Argument(
            help="Setting name",
            show_default=False,
        ),
    ],
    value: Annotated[
        str,
        typer.Option(
            "--value",
            "-v",
            help="Setting value",
            show_default=False,
        ),
    ],
    description: Annotated[
        Optional[str],
        typer.Option(
            "--description",
            "-d",
            help="Setting description",
            show_default=False,
        ),
    ] = None,
):
    """
    Update Setting
    """
    z: ZpodClient = ZpodClient()
    setting = None
    if description is None:
        setting = SettingUpdate(value=value)
    else:
        setting = SettingUpdate(description=description, value=value)

    z.settings_update.sync(body=setting, id=f"name={name}")
    print(
        f"Setting [magenta]{name}[/magenta] has been modified to "
        f"[yellow]{value}[/yellow]."
    )
