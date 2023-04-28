from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from zpod.models.library_create import LibraryCreate
from zpod.models.library_update import LibraryUpdate

from zpodcli.lib import zpod_client

app = typer.Typer(help="Manage libraries")

console = Console()

ZPOD_LIBRARY_DESCRIPTION = "Default zPodFactory library"
ZPOD_LIBRARY_GIT_URL = "https://github.com/zpodfactory/zpodlibrary"


def generate_table(libraries: list, action: str = None):
    title = f"{action} Library"

    table = Table(
        title=title,
        show_header=True,
        header_style="bold cyan",
        title_style="bold green",
    )
    table.add_column("Name")
    table.add_column("Decription", style="dim")
    table.add_column("Git URL")
    table.add_column("Creation Date", style="dim")
    table.add_column("Last Update", style="dim")
    table.add_column("Enabled")
    for library in libraries:
        table.add_row(
            f"[green]{library.name}[/green]",
            f"[magenta]{library.description}[/magenta]",
            library.git_url,
            f"[yellow]{library.creation_date.strftime('%Y-%m-%d %H:%M:%S')}[/yellow]",
            f"[magenta]{library.last_modified_date.strftime('%Y-%m-%d %H:%M:%S')}[/magenta]",  # noqa e501
            library.enabled.__str__(),
        )
    console.print(table)


@app.command()
def list():
    z = zpod_client.ZpodClient()
    libraries = z.libraries_get_all.sync()
    generate_table(libraries=libraries, action="List")


@app.command(no_args_is_help=True)
def create(
    name: str = typer.Option(..., "--name", "-n"),
    git_url: str = typer.Option(ZPOD_LIBRARY_GIT_URL, "--git_url", "-u"),
    description: str = typer.Option(ZPOD_LIBRARY_DESCRIPTION, "--description", "-d"),
):
    z = zpod_client.ZpodClient()
    library_in = LibraryCreate(name=name, description=description, git_url=git_url)
    library = z.libraries_create.sync(json_body=library_in)
    generate_table(libraries=[library], action="Create")


@app.command(no_args_is_help=True)
def delete(
    name: str = typer.Option(..., "--name", "-n"),
):
    z = zpod_client.ZpodClient()
    library = z.libraries_delete.sync(id=f"name={name}")
    if library is None:
        console.print(
            f"Library [magenta]{name}[/magenta] has been deleted successfully",
            style="green",
        )
    else:
        console.print(f"Error {library}", style="red")


@app.command(no_args_is_help=True)
def update(
    enabled: Optional[bool] = typer.Option(None, "--enable/--disable"),
    name: str = typer.Option(..., "--name", "-n"),
    description: str = typer.Option(ZPOD_LIBRARY_DESCRIPTION, "--description", "-d"),
):
    is_enabled = None
    z = zpod_client.ZpodClient()
    if enabled is None:
        library = z.libraries_get.sync(id=f"name={name}")
        is_enabled = library.enabled
    elif enabled:
        is_enabled = True
    else:
        is_enabled = False

    library_in = LibraryUpdate(enabled=is_enabled, description=description)
    if library := z.libraries_update.sync(json_body=library_in, id=f"name={name}"):
        generate_table(libraries=[library], action="Enable")
    else:
        console.print(f"Error {library}", style="red")


@app.command(no_args_is_help=True)
def get(name: str = typer.Option(..., "--name", "-n")):
    z = zpod_client.ZpodClient()
    library = z.libraries_get.sync(id=f"name={name}")
    if library is None:
        console.print(f"Library [magenta]{name}[/magenta] not found", style="red")
        return
    generate_table(libraries=[library], action="Get")
