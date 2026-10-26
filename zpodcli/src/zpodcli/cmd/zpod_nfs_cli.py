from typing import Annotated

import typer
from rich import print
from rich.console import Group

from zpodcli.lib.prompt import confirm
from zpodcli.lib.utils import (
    JsonOption,
    NoColorOption,
    console_print,
    get_boolean_markdown,
    json_print,
)
from zpodcli.lib.utils import ZcliTable as Table
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler
from zpodsdk.models.zpod_nfs_client_add import ZpodNfsClientAdd
from zpodsdk.models.zpod_nfs_create import ZpodNfsCreate
from zpodsdk.models.zpod_nfs_export_removed import ZpodNfsExportRemoved
from zpodsdk.models.zpod_nfs_export_view import ZpodNfsExportView
from zpodsdk.models.zpod_nfs_update import ZpodNfsUpdate

app = typer.Typer(help="Manage NFS exports of zcore", no_args_is_help=True)
client_app = typer.Typer(
    help="Add or remove one client of an export", no_args_is_help=True
)
app.add_typer(client_app, name="client")

ZpodNameArg = Annotated[str, typer.Argument(help="zPod name", show_default=False)]
StorageArg = Annotated[
    str,
    typer.Argument(help="Storage name (STORAGE01, STORAGE02, ...)", show_default=False),
]
FolderArg = Annotated[
    str, typer.Argument(help="Folder of the storage to export", show_default=False)
]
ClientArg = Annotated[
    str,
    typer.Argument(
        help="An IPv4 address, an IPv4 network (10.42.111.0/24) or * for everyone",
        show_default=False,
    ),
]
OptionsOption = Annotated[
    str | None,
    typer.Option(
        "--options",
        "-o",
        help=(
            "exports(5) options for every client, comma-separated "
            "(default: rw,no_subtree_check,no_root_squash)"
        ),
        show_default=False,
    ),
]


def split_clients(clients: list[str] | None) -> list[str]:
    return [c.strip() for item in (clients or []) for c in item.split(",") if c.strip()]


def get_export_kind_markdown(export: ZpodNfsExportView) -> str:
    """protected (NFS-01, the nested ESXi datastore), zcore (zcore-init's
    /etc/exports, read-only here) or user."""
    if export.protected:
        return "[orange3]protected[/orange3]"
    if export.owner == "system":
        return "[grey63]zcore[/grey63]"
    return "[tan]user[/tan]"


def get_clients_markdown(export: ZpodNfsExportView) -> str:
    return "\n".join(
        f"[cornflower_blue]{c.client}[/cornflower_blue]" for c in export.clients
    )


def get_options_markdown(options: str) -> str:
    # no_root_squash is the one that matters: root on a client is root on the folder
    return ",".join(
        f"[dark_orange3]{o}[/dark_orange3]" if o == "no_root_squash" else o
        for o in options.split(",")
    )


def generate_table(exports: list[ZpodNfsExportView], title="zPod NFS Export List"):
    table = Table(
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Path")
    table.add_column("Clients")
    table.add_column("Options")
    table.add_column("Owner")
    table.add_column("Protected")
    table.add_column("Active")
    for export in exports:
        table.add_row(
            f"[bold]{export.path}[/bold]",
            get_clients_markdown(export),
            get_options_markdown(export.options),
            "[grey63]system[/grey63]"
            if export.owner == "system"
            else "[tan]user-defined[/tan]",
            get_boolean_markdown(export.protected)
            if export.protected
            else "[grey50]False[/grey50]",
            get_boolean_markdown(export.active),
        )
    console_print(title, table)


def print_export(export: ZpodNfsExportView | ZpodNfsExportRemoved):
    if isinstance(export, ZpodNfsExportRemoved):
        print(f"  [grey63]{export.message}[/grey63]")
        return
    generate_table([export], title="zPod NFS Export")


@app.command(name="list", no_args_is_help=True)
@unexpected_status_handler
def zpod_nfs_list(
    zpod_name: ZpodNameArg,
    json_: JsonOption = False,
    no_color: NoColorOption = False,
):
    """
    List the NFS exports of zcore: zcore's own (/etc/exports) and the user-defined ones
    """
    z: ZpodClient = ZpodClient()
    exports = z.zpods_nfs_get_all.sync(id=f"name={zpod_name}")
    if json_:
        json_print([e.to_dict() for e in exports])
    else:
        generate_table(exports)


@app.command(name="status", no_args_is_help=True)
@unexpected_status_handler
def zpod_nfs_status(
    zpod_name: ZpodNameArg,
    json_: JsonOption = False,
    no_color: NoColorOption = False,
):
    """
    The NFS server of zcore, and who has each export mounted
    """
    z: ZpodClient = ZpodClient()
    zpod = z.zpods_get.sync(id=f"name={zpod_name}")
    nfs = z.zpods_nfs_status.sync(id=f"name={zpod_name}")
    exports = z.zpods_nfs_get_all.sync(id=f"name={zpod_name}")
    if json_:
        json_print({**nfs.to_dict(), "export_list": [e.to_dict() for e in exports]})
        return

    service = (
        f"[dark_sea_green4]{nfs.service}[/dark_sea_green4]"
        if nfs.service == "active"
        else f"[indian_red]{nfs.service}[/indian_red]"
    )
    summary = " · ".join(
        [
            service,
            "enabled" if nfs.enabled else "[orange3]not enabled[/orange3]",
            f"versions {' '.join(nfs.versions)}",
            f"{nfs.threads} threads" if nfs.threads else "threads ?",
            f"{nfs.exports} exports",
            f"NFS server [magenta]zcore.{zpod.domain}[/magenta]",
        ]
    )

    title = "zPod NFS Status"
    table = Table(
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("NFS Export\n└─ Mounted by")
    table.add_column("Allowed clients\nNFS version")
    table.add_column("Kind")
    v4 = [c for c in nfs.clients if not c.path]
    for export in exports:
        table.add_row(
            f"[bold]{export.path}[/bold]",
            get_clients_markdown(export),
            get_export_kind_markdown(export),
        )
        mounted = [c for c in nfs.clients if c.path == export.path]
        if not mounted:
            table.add_row("[grey50]└─ nobody mounted[/grey50]", "", "")
        for i, c in enumerate(mounted):
            branch = "└─" if i == len(mounted) - 1 else "├─"
            table.add_row(
                f"{branch} [sky_blue2]{c.client}[/sky_blue2]", f"NFSv{c.version}", ""
            )
    if v4:
        table.add_row(
            "[bold]NFSv4 clients[/bold] [grey50](pseudo root)[/grey50]", "", ""
        )
        for i, c in enumerate(v4):
            branch = "└─" if i == len(v4) - 1 else "├─"
            table.add_row(
                f"{branch} [sky_blue2]{c.client}[/sky_blue2]", f"NFSv{c.version}", ""
            )
    lines = [summary]
    if nfs.inactive_exports:
        lines.append(
            "[orange3]in a file but not served: "
            + ", ".join(nfs.inactive_exports)
            + "[/orange3]"
        )
    console_print(title, Group(*lines, table))


@app.command(name="add", no_args_is_help=True)
@unexpected_status_handler
def zpod_nfs_add(
    zpod_name: ZpodNameArg,
    storage: StorageArg,
    folder: FolderArg,
    clients: Annotated[
        list[str] | None,
        typer.Option(
            "--clients",
            "-c",
            help=(
                "Who may mount it, comma-separated or repeated "
                "(default: * (any host that reaches zcore))"
            ),
            show_default=False,
        ),
    ] = None,
    options: OptionsOption = None,
    no_color: NoColorOption = False,
):
    """
    Export a folder of a storage (the folder is created when missing)
    """
    clients = split_clients(clients)
    print(
        f"Adding NFS export [magenta]/FILER/{storage}/{folder}[/magenta] "
        f"on zPod [magenta]{zpod_name}[/magenta]"
    )
    if not clients:
        print(
            "Clients: [cornflower_blue]*[/cornflower_blue]   [grey63](the default: any "
            "host that reaches zcore; narrow it with --clients, nfs client add/remove "
            "or nfs set)[/grey63]"
        )
    z: ZpodClient = ZpodClient()
    export = z.zpods_nfs_add.sync(
        id=f"name={zpod_name}",
        body=ZpodNfsCreate(
            storage=storage,
            folder=folder,
            clients=clients or None,
            options=options,
        ),
    )
    print_export(export)


@app.command(name="set", no_args_is_help=True)
@unexpected_status_handler
def zpod_nfs_set(
    zpod_name: ZpodNameArg,
    storage: StorageArg,
    folder: FolderArg,
    clients: Annotated[
        list[str],
        typer.Option(
            "--clients",
            "-c",
            help="The whole client list, comma-separated or repeated",
            show_default=False,
        ),
    ],
    options: Annotated[
        str | None,
        typer.Option(
            "--options",
            "-o",
            help="exports(5) options for every client (omitted: keep the current ones)",
            show_default=False,
        ),
    ] = None,
    no_color: NoColorOption = False,
):
    """
    Make an export exactly this: clients and options replaced, created when missing
    """
    clients = split_clients(clients)
    print(
        f"Setting NFS export [magenta]/FILER/{storage}/{folder}[/magenta] on zPod "
        f"[magenta]{zpod_name}[/magenta]: {len(clients)} client"
        f"{'s' if len(clients) != 1 else ''}"
        + (f", options {options}" if options else "")
    )
    z: ZpodClient = ZpodClient()
    export = z.zpods_nfs_set.sync(
        id=f"name={zpod_name}",
        storage=storage,
        folder=folder,
        body=ZpodNfsUpdate(clients=clients, options=options),
    )
    print_export(export)


@app.command(name="remove", no_args_is_help=True)
@unexpected_status_handler
def zpod_nfs_remove(
    zpod_name: ZpodNameArg,
    storage: StorageArg,
    folder: FolderArg,
    yes: Annotated[
        bool,
        typer.Option(
            "-y", "--yes", help="Automatic yes to prompts.", show_default=False
        ),
    ] = False,
    no_color: NoColorOption = False,
):
    """
    Stop exporting a folder (the folder and its data stay)
    """
    if not yes:
        confirm(
            f"Stop exporting [magenta]/FILER/{storage}/{folder}[/magenta] of zPod "
            f"[magenta]{zpod_name}[/magenta]? Clients mounted on it lose access; "
            "the folder and its data stay."
        )
    print(
        f"Removing NFS export [magenta]/FILER/{storage}/{folder}[/magenta] from zPod "
        f"[magenta]{zpod_name}[/magenta] (folder and data kept)"
    )
    z: ZpodClient = ZpodClient()
    z.zpods_nfs_remove.sync(id=f"name={zpod_name}", storage=storage, folder=folder)


@client_app.command(name="add", no_args_is_help=True)
@unexpected_status_handler
def zpod_nfs_client_add(
    zpod_name: ZpodNameArg,
    storage: StorageArg,
    folder: FolderArg,
    client: ClientArg,
    no_color: NoColorOption = False,
):
    """
    Allow one more client to mount an export
    """
    print(
        f"Adding client [cornflower_blue]{client}[/cornflower_blue] to export "
        f"[magenta]/FILER/{storage}/{folder}[/magenta] on zPod [magenta]{zpod_name}[/magenta]"
    )
    z: ZpodClient = ZpodClient()
    export = z.zpods_nfs_client_add.sync(
        id=f"name={zpod_name}",
        storage=storage,
        folder=folder,
        body=ZpodNfsClientAdd(client=client),
    )
    print_export(export)


@client_app.command(name="remove", no_args_is_help=True)
@unexpected_status_handler
def zpod_nfs_client_remove(
    zpod_name: ZpodNameArg,
    storage: StorageArg,
    folder: FolderArg,
    client: ClientArg,
    yes: Annotated[
        bool,
        typer.Option(
            "-y", "--yes", help="Automatic yes to prompts.", show_default=False
        ),
    ] = False,
    no_color: NoColorOption = False,
):
    """
    Take one client off an export (the last one removes the export, the folder stays)
    """
    z: ZpodClient = ZpodClient()
    if not yes:
        export = z.zpods_nfs_get.sync(
            id=f"name={zpod_name}", storage=storage, folder=folder
        )
        if [c.client for c in export.clients] == [client]:
            confirm(
                f"[cornflower_blue]{client}[/cornflower_blue] is the last client of "
                f"[magenta]{export.path}[/magenta]: removing it removes the export "
                "(the folder and its data stay). Continue?"
            )
    print(
        f"Removing client [cornflower_blue]{client}[/cornflower_blue] from export "
        f"[magenta]/FILER/{storage}/{folder}[/magenta] on zPod [magenta]{zpod_name}[/magenta]"
    )
    export = z.zpods_nfs_client_remove.sync(
        id=f"name={zpod_name}",
        storage=storage,
        folder=folder,
        client_path=client,
    )
    print_export(export)
