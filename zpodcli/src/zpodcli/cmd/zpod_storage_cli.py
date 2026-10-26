from typing import Annotated

import typer
from rich import print

from zpodcli.cmd import zpod_disk_cli
from zpodcli.cmd.zpod_nfs_cli import get_options_markdown
from zpodcli.lib.prompt import confirm
from zpodcli.lib.utils import (
    JsonOption,
    NoColorOption,
    console_print,
    exit_with_error,
    format_gib,
    json_print,
)
from zpodcli.lib.utils import ZcliTable as Table
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler
from zpodsdk.models.zpod_storage_adopt import ZpodStorageAdopt
from zpodsdk.models.zpod_storage_create import ZpodStorageCreate
from zpodsdk.models.zpod_storage_folder_create import ZpodStorageFolderCreate
from zpodsdk.models.zpod_storage_folder_update import ZpodStorageFolderUpdate
from zpodsdk.models.zpod_storage_operation import ZpodStorageOperation
from zpodsdk.models.zpod_storage_view import ZpodStorageView
from zpodsdk.types import Unset

app = typer.Typer(
    help="Manage the storages of zcore: filesystems mounted under /FILER (sizes in GiB)",
    no_args_is_help=True,
)
folder_app = typer.Typer(help="Manage the folders of a storage", no_args_is_help=True)
app.add_typer(folder_app, name="folder")

KINDS = {"zcore", "user"}

ZpodNameArg = Annotated[str, typer.Argument(help="zPod name", show_default=False)]
StorageArg = Annotated[
    str, typer.Argument(help="Storage name (STORAGE02, ...)", show_default=False)
]
FolderArg = Annotated[str, typer.Argument(help="Folder name", show_default=False)]
DryRunOption = Annotated[
    bool, typer.Option("--dry-run", help="Show the steps with status planned; run none")
]
VerboseOption = Annotated[
    bool, typer.Option("--verbose", help="Show each step's command and output")
]
YesOption = Annotated[
    bool,
    typer.Option("-y", "--yes", help="Automatic yes to prompts.", show_default=False),
]


def value(v):
    return None if isinstance(v, Unset) else v


# ── output ─────────────────────────────────────────────────────────────────────


def usage_bar(used: int, size: int, width: int = 10) -> str:
    pct = used / size if size else 0
    filled = min(width, round(pct * width))
    color = "indian_red" if pct >= 0.9 else "orange3" if pct >= 0.75 else "sky_blue2"
    bar = f"[{color}]{'━' * filled}[/{color}][grey37]{'━' * (width - filled)}[/grey37]"
    if filled == 0:
        bar = f"[{color}]╸[/{color}][grey37]{'━' * (width - 1)}[/grey37]"
    return f"{bar} {pct:5.1%} ({format_gib(used)})"


def access_markdown(options: str) -> str:
    """rw or ro, and no_root_squash called out; the full string is in nfs list."""
    opts = options.split(",")
    access = "ro" if "ro" in opts else "rw"
    if "no_root_squash" in opts:
        return f"{access}, {get_options_markdown('no_root_squash')}"
    return access


def get_kind_markdown(kind: str) -> str:
    match kind:
        case "protected":
            return "[orange3]protected[/orange3]"
        case "zcore":
            return "[grey63]zcore[/grey63]"
        case _:
            return f"[tan]{kind}[/tan]"


def generate_table(storages: list[ZpodStorageView], exports: list, server: str):
    """Layout D (D18): one table, storage values on storage rows, folder values on
    the folder rows hanging under them; two-line headers say which is which."""
    title = "zPod Storage List"
    by_path = {e.path: e for e in exports}
    table = Table(
        title=title,
        title_style="bold",
        caption=None,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Storage\n└─ Folder")
    table.add_column("Used\n")
    table.add_column("Mount · FS\nNFS Export")
    table.add_column("Size\nPartition · Clients")
    table.add_column("Layout · Disk\nVolume · Access")
    table.add_column("Kind\n")
    exported_total = folders_total = 0
    for i, s in enumerate(storages):
        folders = value(s.folders) or []
        exported = sum(1 for f in folders if f.exported)
        exported_total += exported
        folders_total += len(folders)
        lvm = s.layout == "lvm"
        table.add_row(
            f"[bold magenta]{s.name}[/bold magenta] [grey50]{exported}/{len(folders)}"
            f"[/grey50]" + ("\n│" if folders else ""),
            usage_bar(s.used_bytes, s.size_bytes),
            f"[sky_blue2]{s.mountpoint}[/sky_blue2] · {value(s.fstype) or '?'}",
            f"[cornflower_blue]{format_gib(s.size_bytes, whole=True)}[/cornflower_blue]\n"
            f"[grey63]{s.device}[/grey63]",
            f"{s.layout} · /dev/{s.disk}\n"
            + (
                f"[grey63]{value(s.vg)}/{value(s.lv)}[/grey63]"
                if lvm
                else "[grey50]no LVM[/grey50]"
            ),
            get_kind_markdown(str(s.kind)),
            end_section=not folders and i < len(storages) - 1,
        )
        for j, f in enumerate(folders):
            last = j == len(folders) - 1
            branch = "└─" if last else "├─"
            export = by_path.get(f.path)
            kind = "protected" if f.protected else str(s.kind)
            if export:
                clients = "\n".join(c.client for c in export.clients)
                row = (
                    f"[sky_blue2]{f.path}[/sky_blue2]",
                    f"[cornflower_blue]{clients}[/cornflower_blue]",
                    access_markdown(export.options),
                )
            else:
                row = ("[grey50]not exported[/grey50]", "", "")
            table.add_row(
                f"{branch} [bold]{f.name}[/bold]",
                "",
                *row,
                get_kind_markdown(kind),
                end_section=last and i < len(storages) - 1,
            )
    table.caption = (
        f"[grey50]{exported_total}/{folders_total}: folders exported · NFS server "
        f"[/grey50][magenta]{server}[/magenta]"
    )
    console_print(title, table)


def steps_line(result: ZpodStorageOperation) -> str:
    steps = value(result.steps) or []
    names = " · ".join(s.step for s in steps)
    states = {s.status for s in steps}
    status = (
        "planned"
        if result.dry_run
        else "done"
        if states <= {"done", "skipped"}
        else ", ".join(sorted(states))
    )
    return f"  [grey63]{names}[/grey63]: {status}"


def print_steps_verbose(result: ZpodStorageOperation):
    table = Table(show_header=True, header_style="bold cyan")
    for col in ("Step", "Target", "Status", "Command"):
        table.add_column(col)
    for s in value(result.steps) or []:
        table.add_row(s.step, s.target, s.status, value(s.command) or "")
    console_print("zPod Storage Steps", table)


def print_operation(result: ZpodStorageOperation, verbose: bool):
    print(steps_line(result))
    if verbose:
        print_steps_verbose(result)


# ── the storage steps, reused by the composed commands ─────────────────────────


def storage_create(
    zpod_name: str,
    disk: str,
    lvm: bool = False,
    name: str | None = None,
    dry_run: bool = False,
    verbose: bool = False,
) -> ZpodStorageOperation:
    disk = disk.removeprefix("/dev/")
    print(
        f"Creating a storage on [bold]/dev/{disk}[/bold] of zPod "
        f"[magenta]{zpod_name}[/magenta] ({'lvm' if lvm else 'raw'})"
    )
    z: ZpodClient = ZpodClient()
    result = z.zpods_storage_create.sync(
        id=f"name={zpod_name}",
        body=ZpodStorageCreate(disk=disk, lvm=lvm, name=name),
        dry_run=dry_run,
        verbose=verbose,
    )
    print_operation(result, verbose)
    storage = value(result.storage)
    if storage:
        print(
            f"  [bold magenta]{storage.name}[/bold magenta] mounted at "
            f"[sky_blue2]{storage.mountpoint}[/sky_blue2], {format_gib(storage.size_bytes, whole=True)}"
        )
    return result


def storage_grow(
    zpod_name: str, name: str, dry_run: bool = False, verbose: bool = False
) -> ZpodStorageOperation:
    print(
        f"Growing storage [bold magenta]{name}[/bold magenta] of zPod "
        f"[magenta]{zpod_name}[/magenta] into the free space of its disk"
    )
    z: ZpodClient = ZpodClient()
    result = z.zpods_storage_grow.sync(
        id=f"name={zpod_name}", name=name, dry_run=dry_run, verbose=verbose
    )
    print_operation(result, verbose)
    before = getattr(value(result.before), "additional_properties", {})
    after = getattr(value(result.after), "additional_properties", {})
    if dry_run:
        return result
    if value(result.changed) is False:
        print(
            "  [yellow3]nothing to grow: the disk has no free space; grow the disk "
            f"first (zcli zpod disk grow {zpod_name} <device> --size N)[/yellow3]"
        )
    elif before and after:
        key = "filesystem_bytes"
        print(
            f"  [bold magenta]{name}[/bold magenta]: {format_gib(before.get(key), whole=True)} → "
            f"{format_gib(after.get(key), whole=True)}, mounted throughout"
        )
    return result


def storage_delete(
    zpod_name: str, name: str, dry_run: bool = False, verbose: bool = False
) -> ZpodStorageOperation:
    print(
        f"Deleting storage [bold magenta]{name}[/bold magenta] of zPod "
        f"[magenta]{zpod_name}[/magenta]: unmount, mount unit removed; the data stays "
        "on the disk"
    )
    z: ZpodClient = ZpodClient()
    result = z.zpods_storage_delete.sync(
        id=f"name={zpod_name}", name=name, dry_run=dry_run, verbose=verbose
    )
    print_operation(result, verbose)
    return result


# ── commands ─────────────────────────────────────────────────────────────────


@app.command(name="list", no_args_is_help=True)
@unexpected_status_handler
def zpod_storage_list(
    zpod_name: ZpodNameArg,
    kind: Annotated[
        list[str] | None,
        typer.Option(
            "--kind",
            "-k",
            help="Only these kinds: zcore (STORAGE01), user. Repeat or comma-separate.",
            show_default=False,
        ),
    ] = None,
    json_: JsonOption = False,
    no_color: NoColorOption = False,
):
    """
    List the storages of zcore, their folders and how each folder is exported
    """
    kinds = {
        k.strip().lower() for item in (kind or []) for k in item.split(",") if k.strip()
    }
    if unknown := kinds - KINDS:
        exit_with_error(
            f"unknown kind(s): {', '.join(sorted(unknown))}; choose from "
            f"{', '.join(sorted(KINDS))}"
        )
    z: ZpodClient = ZpodClient()
    storages = z.zpods_storages_get_all.sync(id=f"name={zpod_name}")
    if kinds:
        storages = [s for s in storages if str(s.kind) in kinds]
    if json_:
        json_print([s.to_dict() for s in storages])
        return
    zpod = z.zpods_get.sync(id=f"name={zpod_name}")
    exports = z.zpods_nfs_get_all.sync(id=f"name={zpod_name}")
    generate_table(storages, exports, f"zcore.{zpod.domain}")


@app.command(name="create", no_args_is_help=True)
@unexpected_status_handler
def zpod_storage_create(
    zpod_name: ZpodNameArg,
    disk: Annotated[
        str,
        typer.Option(
            "--disk", help="A blank disk of the zPod (/dev/sdc)", show_default=False
        ),
    ],
    lvm: Annotated[
        bool, typer.Option("--lvm", help="One LVM volume on the disk (default: raw)")
    ] = False,
    name: Annotated[
        str | None,
        typer.Option(
            "--name", help="default: the next free STORAGEnn", show_default=False
        ),
    ] = None,
    dry_run: DryRunOption = False,
    verbose: VerboseOption = False,
    no_color: NoColorOption = False,
):
    """
    Partition, format and mount a blank disk as /FILER/STORAGEnn
    """
    storage_create(zpod_name, disk, lvm, name, dry_run, verbose)


@app.command(name="adopt", no_args_is_help=True)
@unexpected_status_handler
def zpod_storage_adopt(
    zpod_name: ZpodNameArg,
    device: Annotated[
        str,
        typer.Option(
            "--device",
            help="The filesystem to mount again (/dev/sdc1, or vg/lv)",
            show_default=False,
        ),
    ],
    name: Annotated[
        str | None,
        typer.Option(
            "--name", help="default: the next free STORAGEnn", show_default=False
        ),
    ] = None,
    dry_run: DryRunOption = False,
    verbose: VerboseOption = False,
    no_color: NoColorOption = False,
):
    """
    Mount an existing filesystem again as a storage (after storage delete), data intact
    """
    z: ZpodClient = ZpodClient()
    result = z.zpods_storage_adopt.sync(
        id=f"name={zpod_name}",
        body=ZpodStorageAdopt(device=device, name=name),
        dry_run=dry_run,
        verbose=verbose,
    )
    print_operation(result, verbose)
    storage = value(result.storage)
    if storage:
        print(
            f"  [bold magenta]{storage.name}[/bold magenta] mounted again at "
            f"[sky_blue2]{storage.mountpoint}[/sky_blue2] from {storage.device}, "
            "data intact"
        )


@app.command(name="grow", no_args_is_help=True)
@unexpected_status_handler
def zpod_storage_grow(
    zpod_name: ZpodNameArg,
    name: StorageArg,
    size: Annotated[
        int | None,
        typer.Option(
            "--size",
            help=(
                "Grow its disk first to this total size, in GiB (zcli zpod disk grow), "
                "then the storage"
            ),
            show_default=False,
        ),
    ] = None,
    dry_run: DryRunOption = False,
    verbose: VerboseOption = False,
    no_color: NoColorOption = False,
):
    """
    Grow a storage into the free space of its disk, online (--size grows the disk first)
    """
    if size is not None:
        z: ZpodClient = ZpodClient()
        storage = z.zpods_storage_get.sync(id=f"name={zpod_name}", name=name)
        zpod_disk_cli.disk_grow(zpod_name, storage.disk, size, hint=False)
    storage_grow(zpod_name, name, dry_run, verbose)


@app.command(name="delete", no_args_is_help=True)
@unexpected_status_handler
def zpod_storage_delete(
    zpod_name: ZpodNameArg,
    name: StorageArg,
    dry_run: DryRunOption = False,
    verbose: VerboseOption = False,
    no_color: NoColorOption = False,
):
    """
    Unmount a storage; its filesystem and data stay on the disk (adopt brings it back)
    """
    z: ZpodClient = ZpodClient()
    storage = z.zpods_storage_get.sync(id=f"name={zpod_name}", name=name)
    result = storage_delete(zpod_name, name, dry_run, verbose)
    if not dry_run:
        print(
            f"  [bold magenta]{name}[/bold magenta] deleted; /dev/{storage.disk} is "
            f"{value(result.disk_state) or 'foreign'} (adopt it with zcli zpod storage "
            f"adopt {zpod_name} --device {storage.device}, or remove it with zcli zpod "
            "disk remove)"
        )


@app.command(name="add", no_args_is_help=True)
@unexpected_status_handler
def zpod_storage_add(
    zpod_name: ZpodNameArg,
    size: Annotated[
        int,
        typer.Option(
            "--size",
            help="Size of the new disk, in GiB (whole number, e.g. 500)",
            show_default=False,
        ),
    ],
    lvm: Annotated[
        bool, typer.Option("--lvm", help="One LVM volume on the disk (default: raw)")
    ] = False,
    name: Annotated[
        str | None,
        typer.Option(
            "--name", help="default: the next free STORAGEnn", show_default=False
        ),
    ] = None,
    no_color: NoColorOption = False,
):
    """
    A new disk and a storage on it, in one command (disk add, then storage create)
    """
    disk = zpod_disk_cli.disk_add(zpod_name, size)
    device = value(disk.device) if disk else None
    if not device:
        exit_with_error(
            "the disk was added but zcore does not show it: no storage created"
        )
    try:
        storage_create(zpod_name, device, lvm, name)
    except Exception:
        print(
            f"  [yellow3]{device} stays, blank: retry zcli zpod storage create "
            f"{zpod_name} --disk {device}, or remove it with zcli zpod disk remove[/yellow3]"
        )
        raise


@app.command(name="remove", no_args_is_help=True)
@unexpected_status_handler
def zpod_storage_remove(
    zpod_name: ZpodNameArg,
    name: StorageArg,
    yes: YesOption = False,
    no_color: NoColorOption = False,
):
    """
    Delete a storage and remove its disk with all its data, in one command
    """
    z: ZpodClient = ZpodClient()
    storage = z.zpods_storage_get.sync(id=f"name={zpod_name}", name=name)
    if not yes:
        confirm(
            f"This deletes storage [bold magenta]{name}[/bold magenta] and its disk "
            f"[bold]/dev/{storage.disk}[/bold] with the {format_gib(storage.size_bytes, whole=True)} "
            "on it. Are you sure?"
        )
    storage_delete(zpod_name, name)
    zpod_disk_cli.disk_remove(zpod_name, storage.disk, yes=True)


# ── folders ──────────────────────────────────────────────────────────────────


@folder_app.command(name="list", no_args_is_help=True)
@unexpected_status_handler
def zpod_storage_folder_list(
    zpod_name: ZpodNameArg,
    name: StorageArg,
    json_: JsonOption = False,
    no_color: NoColorOption = False,
):
    """
    List the folders of a storage
    """
    z: ZpodClient = ZpodClient()
    storage = z.zpods_storage_get.sync(id=f"name={zpod_name}", name=name)
    folders = value(storage.folders) or []
    if json_:
        json_print([f.to_dict() for f in folders])
        return
    title = "zPod Storage Folder List"
    table = Table(title=title, title_style="bold", header_style="bold cyan")
    for col in ("Folder", "Path", "Owner", "Mode", "Empty", "Exported", "Kind"):
        table.add_column(col)
    for f in folders:
        table.add_row(
            f"[bold]{f.name}[/bold]",
            f"[sky_blue2]{f.path}[/sky_blue2]",
            f.owner,
            f.mode,
            str(f.empty),
            "[dark_sea_green4]True[/dark_sea_green4]"
            if f.exported
            else "[grey50]False[/grey50]",
            get_kind_markdown("protected" if f.protected else str(storage.kind)),
        )
    console_print(title, table)


@folder_app.command(name="add", no_args_is_help=True)
@unexpected_status_handler
def zpod_storage_folder_add(
    zpod_name: ZpodNameArg,
    name: StorageArg,
    folder: FolderArg,
    owner: Annotated[
        str | None,
        typer.Option(
            "--owner", help="user:group (default root:root)", show_default=False
        ),
    ] = None,
    mode: Annotated[
        str | None,
        typer.Option("--mode", help="octal (default 0777)", show_default=False),
    ] = None,
    no_color: NoColorOption = False,
):
    """
    Add a folder to a storage
    """
    z: ZpodClient = ZpodClient()
    view = z.zpods_storage_folder_add.sync(
        id=f"name={zpod_name}",
        name=name,
        folder=folder,
        body=ZpodStorageFolderCreate(owner=owner, mode=mode),
    )
    print(
        f"Added folder [bold]{folder}[/bold] to storage [bold magenta]{name}[/bold magenta] "
        f"of zPod [magenta]{zpod_name}[/magenta] ({view.owner}, {view.mode})"
    )


@folder_app.command(name="set", no_args_is_help=True)
@unexpected_status_handler
def zpod_storage_folder_set(
    zpod_name: ZpodNameArg,
    name: StorageArg,
    folder: FolderArg,
    owner: Annotated[
        str | None, typer.Option("--owner", help="user:group", show_default=False)
    ] = None,
    mode: Annotated[
        str | None, typer.Option("--mode", help="octal", show_default=False)
    ] = None,
    recursive: Annotated[
        bool, typer.Option("--recursive", help="Everything below the folder too")
    ] = False,
    no_color: NoColorOption = False,
):
    """
    Change the owner and/or mode of a folder
    """
    if owner is None and mode is None:
        exit_with_error("give --owner, --mode, or both")
    print(
        f"Setting folder [bold]{folder}[/bold] of [bold magenta]{name}[/bold magenta]: "
        + ", ".join(
            x
            for x in (
                f"owner {owner}" if owner else "",
                f"mode {mode}" if mode else "",
                "recursive" if recursive else "",
            )
            if x
        )
    )
    z: ZpodClient = ZpodClient()
    z.zpods_storage_folder_set.sync(
        id=f"name={zpod_name}",
        name=name,
        folder=folder,
        body=ZpodStorageFolderUpdate(owner=owner, mode=mode, recursive=recursive),
    )


@folder_app.command(name="remove", no_args_is_help=True)
@unexpected_status_handler
def zpod_storage_folder_remove(
    zpod_name: ZpodNameArg,
    name: StorageArg,
    folder: FolderArg,
    force: Annotated[
        bool,
        typer.Option("--force", help="Delete the folder with everything in it"),
    ] = False,
    yes: YesOption = False,
    no_color: NoColorOption = False,
):
    """
    Remove a folder that is not exported (--force when it is not empty)
    """
    if force and not yes:
        confirm(
            f"This deletes [bold]/FILER/{name}/{folder}[/bold] with everything in it. "
            "Are you sure?"
        )
    z: ZpodClient = ZpodClient()
    removed = z.zpods_storage_folder_remove.sync(
        id=f"name={zpod_name}", name=name, folder=folder, force=force
    )
    print(
        f"Removed folder [bold]{removed.path}[/bold] "
        f"[grey63]({removed.removed} file(s) and folder(s))[/grey63]"
    )
