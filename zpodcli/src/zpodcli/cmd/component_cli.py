import os

import typer
from rich.progress import Progress
from rich.table import Table
from typing_extensions import Annotated

from zpodcli.lib.utils import console_print, exit_with_error
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler

CHUNK_SIZE = 1024 * 1024 * 16  # 16MB

app = typer.Typer(help="Manage Components")


def get_status_markdown(status: str):
    match status:
        case "NOT_STARTED" | "INACTIVE":
            return f"[grey63]{status}[/grey63]"
        case "SCHEDULED":
            return "[royal_blue1]SCHEDULED[/royal_blue1]"
        case "VERIFYING_CHECKSUM":
            return "[deep_sky_blue1]Verifying Checksum...[/deep_sky_blue1]"
        case "COMPLETED" | "ACTIVE" | "DOWNLOAD_COMPLETED":
            return f"[dark_sea_green4]{status}[/dark_sea_green4]"
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
    table.add_column("Download Status")
    table.add_column("Status")

    for component in components:
        table.add_row(
            f"[yellow3]{component.component_uid}[/yellow3]",
            f"[medium_purple1]{component.component_name}[/medium_purple1]",
            f"[cornflower_blue]{component.component_version}[/cornflower_blue]",
            f"[green]{component.library_name}[/green]",
            component.component_description,
            get_status_markdown(component.download_status),
            get_status_markdown(component.status),
        )
    console_print(title, table)


@app.command(name="list")
@unexpected_status_handler
def component_list(
    all_: Annotated[
        bool,
        typer.Option(
            "--all",
            "-a",
            help="Show all library components",
        ),
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
    if not all_:
        filtered_components.extend(
            c
            for c in sorted_components
            if c.download_status == "SCHEDULED"
            or c.download_status.isdigit()  # Download percentage value
            or c.download_status == "VERIFYING_CHECKSUM"
            or c.status == "ACTIVE"
        )

        sorted_components = filtered_components

    generate_table(sorted_components)


@app.command(name="enable", no_args_is_help=True)
@unexpected_status_handler
def component_enable(
    component_uid: Annotated[
        str,
        typer.Argument(
            help="Component UID",
            show_default=False,
        ),
    ],
):
    """
    Enable Component
    """

    z: ZpodClient = ZpodClient()
    component = z.components_enable.sync(id=f"uid={component_uid}")
    generate_table(
        components=[component],
        component_uid=component_uid,
        action="Enable",
    )


@app.command(name="get", no_args_is_help=True)
@unexpected_status_handler
def component_get(
    component_uid: Annotated[
        str,
        typer.Argument(
            help="Component UID",
            show_default=False,
        ),
    ],
):
    """
    Get Specific Component Information
    """

    z: ZpodClient = ZpodClient()
    component = z.components_get.sync(id=f"uid={component_uid}")

    generate_table(
        components=[component],
        component_uid=component_uid,
        action="Get",
    )


@app.command(name="disable", no_args_is_help=True)
@unexpected_status_handler
def component_disable(
    component_uid: Annotated[
        str,
        typer.Argument(
            help="Component UID",
            show_default=False,
        ),
    ],
):
    """
    Disable Specific Component
    """

    z: ZpodClient = ZpodClient()
    component = z.components_disable.sync(id=f"uid={component_uid}")
    generate_table(
        components=[component],
        component_uid=component_uid,
        action="Disable",
    )


@app.command(name="upload", no_args_is_help=True)
@unexpected_status_handler
def component_upload(
    filename: Annotated[
        str,
        typer.Argument(
            help="File to upload",
            show_default=False,
        ),
    ],
):
    """
    Upload a file that represents a component
    """

    z: ZpodClient = ZpodClient()

    client = z._client.get_httpx_client()

    file_size = os.path.getsize(filename)
    basename = os.path.basename(filename)
    offset = get_server_file_size(basename)

    with open(filename, "rb") as file, Progress() as progress:
        file.seek(offset)
        task = progress.add_task(f"Uploading {filename}", total=file_size)
        progress.update(task, advance=offset)

        while True:
            chunk = file.read(CHUNK_SIZE)
            if not chunk:
                break

            response = client.post(
                "/components/upload",
                files={"file": chunk},
                data={
                    "filename": basename,
                    "offset": offset,
                    "file_size": file_size,
                },
            )

            if response.status_code != 200:
                exit_with_error("Error uploading file.")

            offset += len(chunk)
            progress.update(task, advance=len(chunk))


def get_server_file_size(filename: str) -> int:
    z: ZpodClient = ZpodClient()

    client = z._client.get_httpx_client()

    response = client.get(f"/components/upload/{os.path.basename(filename)}")
    if response.status_code == 200:
        return response.json().get("current_size", 0)
    return 0
