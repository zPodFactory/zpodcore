import time
from typing import Annotated

import typer
from rich import print
from rich.console import Console

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
from zpodsdk.models.zpod_disk_create import ZpodDiskCreate
from zpodsdk.models.zpod_disk_grow import ZpodDiskGrow
from zpodsdk.models.zpod_disk_run_view import ZpodDiskRunView
from zpodsdk.models.zpod_disk_view import ZpodDiskView
from zpodsdk.types import Unset

app = typer.Typer(
    help="Manage the virtual disks of zcore (sizes in GiB)", no_args_is_help=True
)

KINDS = {"zpod", "user"}
FINAL_RUN_STATES = ("COMPLETED", "FAILED", "CRASHED", "CANCELLED")

ZpodNameArg = Annotated[str, typer.Argument(help="zPod name", show_default=False)]
DeviceArg = Annotated[
    str, typer.Argument(help="Disk device on zcore (/dev/sdc)", show_default=False)
]
WaitOption = Annotated[
    bool,
    typer.Option(
        "--wait/--no-wait",
        help="Follow the zpodengine run and print how it ended (default: wait)",
    ),
]


def value(v):
    return None if isinstance(v, Unset) else v


def get_state_markdown(state: str | None) -> str:
    match state:
        case "blank":
            return f"[dark_sea_green4]{state}[/dark_sea_green4]"
        case "in-use":
            return f"[sky_blue2]{state}[/sky_blue2]"
        case "protected" | "system":
            return f"[grey63]{state}[/grey63]"
        case "foreign":
            return f"[orange3]{state}[/orange3]"
        case None:
            return "[grey50]?[/grey50]"
        case _:
            return state


def get_kind_markdown(kind: str) -> str:
    return (
        f"[tan]{kind}[/tan]" if kind == "user" else f"[dark_khaki]{kind}[/dark_khaki]"
    )


def get_disk_status_markdown(status: str) -> str:
    match status:
        case "ACTIVE":
            return f"[dark_sea_green4]{status}[/dark_sea_green4]"
        case "PENDING":
            return f"[grey63]{status}...[/grey63]"
        case "MISSING":
            return f"[indian_red]{status}[/indian_red]"
        case _:
            return f"[royal_blue1]{status}[/royal_blue1]"


def generate_table(disks: list[ZpodDiskView], title="zPod Disk List"):
    table = Table(
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Device")
    table.add_column("SCSI")
    table.add_column("Size", justify="right")
    table.add_column("State")
    table.add_column("Storage")
    table.add_column("Kind")
    table.add_column("Status")
    for disk in disks:
        table.add_row(
            f"[bold]{value(disk.device) or '?'}[/bold]",
            f"[yellow3]{value(disk.scsi) or '-'}[/yellow3]",
            f"[cornflower_blue]{format_gib(gib=disk.size_gb)}[/cornflower_blue]",
            get_state_markdown(value(disk.state)),
            f"[magenta]{value(disk.storage)}[/magenta]" if value(disk.storage) else "-",
            get_kind_markdown(str(disk.kind)),
            get_disk_status_markdown(str(disk.status)),
        )
    console_print(title, table)


def device_name(device: str) -> str:
    return device.removeprefix("/dev/")


def follow_disk_run(
    z: ZpodClient, zpod_name: str, flow_run_id: str, what: str
) -> ZpodDiskRunView:
    """Poll the disk run until it ends. Ctrl-C leaves it running."""
    console = Console()
    try:
        with console.status(
            f"[grey63]{what}: running in zpodengine...[/grey63]", spinner="dots"
        ):
            while True:
                run: ZpodDiskRunView = z.zpods_disk_run.sync(
                    id=f"name={zpod_name}", flow_run_id=flow_run_id
                )
                if run.state in FINAL_RUN_STATES:
                    return run
                time.sleep(3)
    except KeyboardInterrupt:
        print(
            f"  still running in zpodengine: run [grey50]{flow_run_id}[/grey50]; "
            f"zcli zpod disk list {zpod_name} shows the outcome"
        )
        raise typer.Exit() from None


def report_run(started: ZpodDiskRunView, z, zpod_name, what, wait) -> ZpodDiskRunView:
    """Print the run line, follow it, print how it ended; exit 1 when it failed.
    Answers the final run (the disk as it is now)."""
    print(
        f"  status: [grey63]PENDING...[/grey63]  flow run [sky_blue2]{what}[/sky_blue2] "
        f"[grey50]{started.flow_run_id}[/grey50]"
    )
    if not wait:
        return started
    run = follow_disk_run(z, zpod_name, started.flow_run_id, what)
    if run.state != "COMPLETED":
        print(f"  status: [indian_red]{run.state}[/indian_red]")
        if value(run.message):
            print(f"  [indian_red]{run.message}[/indian_red]")
        raise typer.Exit(1)
    return run


def disk_line(disk: ZpodDiskView | None) -> str:
    if disk is None:
        return "  disk removed"
    storage = value(disk.storage)
    return (
        f"  status: {get_disk_status_markdown(str(disk.status))}  "
        f"[bold]{value(disk.device) or '?'}[/bold]  "
        f"{format_gib(gib=disk.size_gb)}  {get_state_markdown(value(disk.state))}"
        + (f" ([magenta]{storage}[/magenta])" if storage else "")
    )


def disk_add(zpod_name: str, size: int, wait: bool = True) -> ZpodDiskView | None:
    print(
        f"Adding a disk of [cornflower_blue]{format_gib(gib=size)}[/cornflower_blue] "
        f"to the zcore VM of zPod [magenta]{zpod_name}[/magenta]"
    )
    z: ZpodClient = ZpodClient()
    started = z.zpods_disk_add.sync(
        id=f"name={zpod_name}", body=ZpodDiskCreate(size_gb=size)
    )
    run = report_run(started, z, zpod_name, f"add disk {zpod_name}/{size}GiB", wait)
    if wait:
        print(disk_line(value(run.disk)))
    return value(run.disk) if wait else None


def disk_grow(zpod_name: str, device: str, size: int, wait: bool = True):
    name = device_name(device)
    z: ZpodClient = ZpodClient()
    current = z.zpods_disk_get.sync(id=f"name={zpod_name}", device=name)
    print(
        f"Growing disk [bold]/dev/{name}[/bold] of zPod [magenta]{zpod_name}[/magenta] "
        f"from {format_gib(gib=current.size_gb)} to "
        f"[cornflower_blue]{format_gib(gib=size)}[/cornflower_blue]"
    )
    started = z.zpods_disk_grow.sync(
        id=f"name={zpod_name}", device=name, body=ZpodDiskGrow(size_gb=size)
    )
    run = report_run(started, z, zpod_name, f"grow disk {zpod_name}/{name}", wait)
    if not wait:
        return None
    disk = value(run.disk)
    print(disk_line(disk))
    if disk and value(disk.storage):
        print(
            f"  [yellow3]{disk.storage} still has its previous size: run zcli zpod "
            f"storage grow {zpod_name} {disk.storage} to use the space[/yellow3]"
        )
    return disk


def disk_remove(zpod_name: str, device: str, yes: bool, wait: bool = True):
    name = device_name(device)
    z: ZpodClient = ZpodClient()
    current = z.zpods_disk_get.sync(id=f"name={zpod_name}", device=name)
    if not yes:
        confirm(
            f"This deletes the virtual disk [bold]/dev/{name}[/bold] and the "
            f"{format_gib(gib=current.size_gb)} on it. Are you sure?"
        )
    print(
        f"Removing disk [bold]/dev/{name}[/bold] from the zcore VM of zPod "
        f"[magenta]{zpod_name}[/magenta]"
    )
    started = z.zpods_disk_remove.sync(id=f"name={zpod_name}", device=name)
    report_run(started, z, zpod_name, f"remove disk {zpod_name}/{name}", wait)
    if wait:
        print("  disk removed")


@app.command(name="list", no_args_is_help=True)
@unexpected_status_handler
def zpod_disk_list(
    zpod_name: ZpodNameArg,
    kind: Annotated[
        list[str] | None,
        typer.Option(
            "--kind",
            "-k",
            help=(
                "Only these kinds: zpod (the deploy's system and filer disks), user. "
                "Repeat the option or give a comma-separated list."
            ),
            show_default=False,
        ),
    ] = None,
    json_: JsonOption = False,
    no_color: NoColorOption = False,
):
    """
    List the virtual disks of zcore and what zcore sees on them (sizes in GiB)
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
    disks: list[ZpodDiskView] = z.zpods_disks_get_all.sync(id=f"name={zpod_name}")
    if kinds:
        disks = [d for d in disks if str(d.kind) in kinds]
    if json_:
        json_print([d.to_dict() for d in disks])
    else:
        generate_table(disks)


@app.command(name="add", no_args_is_help=True)
@unexpected_status_handler
def zpod_disk_add(
    zpod_name: ZpodNameArg,
    size: Annotated[
        int,
        typer.Option(
            "--size",
            help=(
                "Size of the new disk, in GiB (whole number, e.g. 500); at most "
                "zpodfactory_zpod_disk_max_gb"
            ),
            show_default=False,
        ),
    ],
    wait: WaitOption = True,
    no_color: NoColorOption = False,
):
    """
    Add a thin virtual disk to zcore, blank, ready for a storage or anything else
    """
    disk_add(zpod_name, size, wait)


@app.command(name="grow", no_args_is_help=True)
@unexpected_status_handler
def zpod_disk_grow(
    zpod_name: ZpodNameArg,
    device: DeviceArg,
    size: Annotated[
        int,
        typer.Option(
            "--size",
            help="New total size of the disk, in GiB; larger than the current size",
            show_default=False,
        ),
    ],
    wait: WaitOption = True,
    no_color: NoColorOption = False,
):
    """
    Grow a virtual disk of zcore (what is on it grows with zcli zpod storage grow)
    """
    disk_grow(zpod_name, device, size, wait)


@app.command(name="remove", no_args_is_help=True)
@unexpected_status_handler
def zpod_disk_remove(
    zpod_name: ZpodNameArg,
    device: DeviceArg,
    yes: Annotated[
        bool,
        typer.Option(
            "-y", "--yes", help="Automatic yes to prompts.", show_default=False
        ),
    ] = False,
    wait: WaitOption = True,
    no_color: NoColorOption = False,
):
    """
    Remove a blank or foreign disk you added, with its data (refused while in use)
    """
    disk_remove(zpod_name, device, yes, wait)
