from typing import Annotated, Optional

import typer
from rich import print
from rich.table import Table

from zpodcli.lib.utils import console_print, json_print
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler
from zpodsdk.models.setting_create import SettingCreate
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


@app.command(name="create", no_args_is_help=True)
@unexpected_status_handler
def setting_create(
    name: Annotated[
        str,
        typer.Option(
            "--name",
            "-n",
            help="Setting Name",
            show_default=False,
        ),
    ],
    value: Annotated[
        str,
        typer.Option(
            "--value",
            "-v",
            help="Setting Value",
            show_default=False,
        ),
    ],
    description: Annotated[
        str,
        typer.Option(
            "--description",
            "-d",
            help="Setting Description",
            show_default=False,
        ),
    ] = None,
):
    """
    Create Setting
    """
    z: ZpodClient = ZpodClient()
    setting = SettingCreate(name=name, value=value, description=description)
    z.settings_create.sync(body=setting)
    print(
        f"Setting [magenta]{name}[/magenta] has been created "
        f"with value [magenta]{value}[/magenta]."
    )


@app.command(name="list")
@unexpected_status_handler
def setting_list(
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
):
    """
    List Settings
    """
    z: ZpodClient = ZpodClient()
    settings = z.settings_get_all.sync()

    if json_:
        settings_dict = [setting.to_dict() for setting in settings]
        json_print(settings_dict, no_color=no_color)
    else:
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


@app.command(name="delete", no_args_is_help=True)
@unexpected_status_handler
def setting_delete(
    name: Annotated[
        str,
        typer.Argument(
            help="Setting Name",
            show_default=False,
        ),
    ],
):
    """
    Delete Setting
    """
    z: ZpodClient = ZpodClient()
    z.settings_delete.sync(id=f"name={name}")
    print(f"Setting [magenta]{name}[/magenta] has been deleted.")
