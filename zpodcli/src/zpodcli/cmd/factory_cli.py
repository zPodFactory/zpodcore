import re
from typing import Optional

import typer
from rich import print
from rich.table import Table
from typing_extensions import Annotated

from zpodcli.lib.factory_config import FactoryConfig
from zpodcli.lib.utils import console_print, exit_with_error

app = typer.Typer(help="Manage Factories")


def get_status_markdown(status: bool):
    if status:
        return f"[dark_sea_green4]{status}[/dark_sea_green4]"
    return f"[indian_red]{status}[/indian_red]"


def validate_name(value):
    if re.match(r"^[A-Za-z0-9-]*$", value):
        return value.lower()
    raise typer.BadParameter("Invalid character in name")


def validate_server(value):
    if not value:
        return value
    if re.match(r"^(http://)|(https://)[A-Za-z0-9-.]*$", value):
        return value.lower()
    raise typer.BadParameter("Must start with either http:// or https://")


@app.command(name="list")
def factory_list():
    """
    List Factories
    """

    title = "Factory List"
    table = Table(
        "Name",
        "Server",
        "Token",
        "Active Context",
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )

    fc = FactoryConfig()
    for section in sorted(fc.config.sections()):
        factory = fc.config[section]
        token = factory["zpod_api_token"]
        table.add_row(
            f"[tan]{section}[/tan]",
            f"[sky_blue2]{factory['zpod_api_url']}[/sky_blue2]",
            f"{token[:5]}...{token[-5:]}",
            get_status_markdown(factory.getboolean("active", False)),
        )
    console_print(title, table)


@app.command(name="add", no_args_is_help=True)
def factory_add(
    *,
    factory_name: Annotated[
        str,
        typer.Argument(
            help="Factory name",
            show_default=False,
            callback=validate_name,
        ),
    ],
    server: Annotated[
        str,
        typer.Option(
            "--server",
            "-s",
            help="Factory server",
            show_default=False,
            callback=validate_server,
        ),
    ],
    token: Annotated[
        str,
        typer.Option(
            "--token",
            "-t",
            help="Factory token",
            show_default=False,
        ),
    ],
    setactive: Annotated[
        bool,
        typer.Option(
            "--setactive",
            "-a",
            help="Set as active",
        ),
    ] = False,
):
    """
    Add Factory
    """

    print(f"Adding Factory: {factory_name}")

    fc = FactoryConfig()
    factory_names = fc.config.sections()
    if factory_name in factory_names:
        exit_with_error(f"Duplicate factory name found: {factory_name}")

    fc.config.add_section(factory_name)
    factory = fc.config[factory_name]
    factory["zpod_api_url"] = server
    factory["zpod_api_token"] = token
    if setactive or len(factory_names) == 1:
        fc.setactive(factory_name)
    else:
        factory["active"] = "False"
    fc.write()
    factory_list()


@app.command(name="update", no_args_is_help=True)
def factory_update(
    *,
    factory_name: Annotated[
        Optional[str],
        typer.Argument(
            help="Factory name",
            show_default=False,
            callback=validate_name,
        ),
    ],
    newname: Annotated[
        Optional[str],
        typer.Option(
            "--newname",
            callback=validate_name,
            help="New factory name",
        ),
    ] = "",
    server: Annotated[
        Optional[str],
        typer.Option(
            "--server",
            "-s",
            callback=validate_server,
            help="Factory server",
        ),
    ] = "",
    token: Annotated[
        Optional[str],
        typer.Option(
            "--token",
            "-t",
            help="Factory token",
        ),
    ] = "",
    setactive: Annotated[
        bool,
        typer.Option(
            "--setactive",
            "-a",
            help="Set as active",
        ),
    ] = False,
):
    """
    Update Factory
    """
    print(f"Updating factory: {factory_name}")

    fc = FactoryConfig()
    factory_names = fc.config.sections()
    if factory_name not in factory_names:
        exit_with_error(f"Factory name not found: {factory_name}")
    if newname:
        print(f"  Renaming factory to {newname}")
        if newname in factory_names:
            exit_with_error(f"Duplicate factory name found: {newname}")

    factory = fc.config[factory_name]
    if server:
        factory["zpod_api_url"] = server
    if token:
        factory["zpod_api_token"] = token
    if setactive:
        fc.setactive(factory_name)

    if newname:
        fc.config.add_section(newname)
        newfactory = fc.config[newname]
        for key, value in factory.items():
            newfactory[key] = value
        fc.config.remove_section(factory_name)

    fc.write()
    factory_list()


@app.command(name="remove", no_args_is_help=True)
def factory_remove(
    *,
    factory_name: Annotated[
        str,
        typer.Argument(
            help="Factory name",
            show_default=False,
            callback=validate_name,
        ),
    ],
):
    """
    Remove Factory
    """
    print(f"Removing Factory: {factory_name}")

    fc = FactoryConfig()
    if factory_name not in fc.config.sections():
        exit_with_error(f"Factory name not found: {factory_name}")

    factory = fc.config[factory_name]
    if factory.getboolean("active"):
        exit_with_error(f"Cannot remove active factory: {factory_name}")

    fc.config.remove_section(factory_name)
    fc.write()
    factory_list()
