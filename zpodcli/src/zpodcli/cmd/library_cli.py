from typing import Optional

import typer
from rich.table import Table
from typing_extensions import Annotated

from zpodcli.lib.utils import console_print, get_boolean_markdown
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler
from zpodsdk.models.library_create import LibraryCreate
from zpodsdk.models.library_update import LibraryUpdate

app = typer.Typer(help="Manage Libraries")


def generate_table(libraries: list, action: str = None):
    title = f"Library {action}"

    table = Table(
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Git URL")
    table.add_column("Creation Date")
    table.add_column("Last Update")
    table.add_column("Enabled")
    for library in libraries:
        table.add_row(
            f"[green]{library.name}[/green]",
            library.description,
            f"[sky_blue2]{library.git_url}[/sky_blue2]",
            f"[tan]{library.creation_date.strftime('%Y-%m-%d %H:%M:%S')}[/tan]",
            f"[magenta]{library.last_modified_date.strftime('%Y-%m-%d %H:%M:%S')}[/magenta]",  # noqa e501
            get_boolean_markdown(library.enabled),
        )
    console_print(title, table)


@app.command(name="list")
@unexpected_status_handler
def library_list():
    """
    List Libraries
    """
    z: ZpodClient = ZpodClient()
    libraries = z.libraries_get_all.sync()
    generate_table(libraries=libraries, action="List")


@app.command(name="create", no_args_is_help=True)
@unexpected_status_handler
def library_create(
    library_name: Annotated[
        str,
        typer.Argument(
            help="Library name",
            show_default=False,
        ),
    ],
    git_url: Annotated[
        str,
        typer.Option(
            "--git-url",
            "-u",
            help="Library git URL",
            show_default=False,
        ),
    ] = "",
    description: Annotated[
        str,
        typer.Option(
            "--description",
            "-d",
            help="Library description",
            show_default=False,
        ),
    ] = "",
):
    """
    Create Library
    """
    z: ZpodClient = ZpodClient()
    library_in = LibraryCreate(
        name=library_name, description=description, git_url=git_url
    )
    library = z.libraries_create.sync(body=library_in)
    generate_table(libraries=[library], action="Create")


@app.command(name="delete", no_args_is_help=True)
@unexpected_status_handler
def library_delete(
    library_name: Annotated[
        str,
        typer.Argument(
            help="Library name",
            show_default=False,
        ),
    ],
):
    """
    Delete Library
    """
    z: ZpodClient = ZpodClient()
    z.libraries_delete.sync(id=f"name={library_name}")
    print(
        f"Library [magenta]{library_name}[/magenta] has been deleted successfully.",
    )


@app.command(name="update", no_args_is_help=True)
@unexpected_status_handler
def library_update(
    *,
    library_name: Annotated[
        str,
        typer.Argument(
            help="Library name",
            show_default=False,
        ),
    ],
    description: Annotated[
        str,
        typer.Option(
            "--description",
            "-d",
            help="Library description",
            show_default=False,
        ),
    ] = "",
    enabled: Annotated[
        Optional[bool],
        typer.Option(
            "--enable/--disable",
            help="Enable or disable library",
            show_default=False,
        ),
    ] = None,
):
    """
    Update Library Metadata (Description and Enabled/Disabled)
    """
    is_enabled = None
    z: ZpodClient = ZpodClient()
    if enabled is None:
        library = z.libraries_get.sync(id=f"name={library_name}")
        is_enabled = library.enabled
    elif enabled:
        is_enabled = True
    else:
        is_enabled = False

    library_in = LibraryUpdate(enabled=is_enabled, description=description)
    z.libraries_update.sync(body=library_in, id=f"name={library_name}")
    generate_table(libraries=[library], action="Enable")


@app.command(name="get", no_args_is_help=True)
@unexpected_status_handler
def library_get(
    library_name: Annotated[
        str,
        typer.Argument(
            help="Library name",
            show_default=False,
        ),
    ],
):
    """
    Get Library
    """
    z: ZpodClient = ZpodClient()
    library = z.libraries_get.sync(id=f"name={library_name}")
    generate_table(libraries=[library], action="Get")


@app.command(name="resync", no_args_is_help=True)
@unexpected_status_handler
def library_resync(
    library_name: Annotated[
        str,
        typer.Argument(
            help="Library name",
            show_default=False,
        ),
    ],
):
    """
    Resync Libraries (Will refresh *ALL* library components json/metadata)
    """
    z: ZpodClient = ZpodClient()
    library = z.libraries_resync.sync(id=f"name={library_name}")
    generate_table(libraries=[library], action="Sync")
