from typing import List

import typer
from rich import print
from rich.table import Table
from typing_extensions import Annotated

from zpodcli.lib.prompt import confirm
from zpodcli.lib.utils import console_print, exit_with_error
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler
from zpodsdk.models.zpod_dns_create import ZpodDnsCreate
from zpodsdk.models.zpod_dns_update import ZpodDnsUpdate
from zpodsdk.models.zpod_dns_view import ZpodDnsView

app = typer.Typer(help="Manage zPod DNS", no_args_is_help=True)


def generate_table(
    zpod_dns: list[ZpodDnsView],
):
    title = "zPod DNS List"

    table = Table(
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("IP")
    table.add_column("Hostname")

    for item in zpod_dns:
        table.add_row(
            f"[sky_blue2]{item.ip}[/sky_blue2]",
            f"[sky_blue2]{item.hostname}[/sky_blue2]",
        )

    console_print(title, table)


@app.command(name="list", no_args_is_help=True)
@unexpected_status_handler
def zpod_dns_list(
    zpod_name: Annotated[
        str,
        typer.Argument(
            help="zPod name",
            show_default=False,
        ),
    ],
):
    """
    List DNS records for zPod
    """
    print(f"Listing {zpod_name} DNS")
    z: ZpodClient = ZpodClient()
    zpod_dns: List[ZpodDnsView] = z.zpods_dns_get_all.sync(id=f"name={zpod_name}")
    generate_table(zpod_dns)


@app.command(name="add", no_args_is_help=True)
@unexpected_status_handler
def zpod_dns_add(
    zpod_name: Annotated[
        str,
        typer.Argument(
            help="zPod name",
            show_default=False,
        ),
    ],
    hostname: Annotated[
        str,
        typer.Option(
            "--hostname",
            help="Hostname",
            show_default=False,
        ),
    ],
    ip: Annotated[
        str,
        typer.Option(
            "--ip",
            help="IP Address",
            show_default=False,
        ),
    ] = None,
    host_id: Annotated[
        int,
        typer.Option(
            "--host-id",
            help="Host ID",
            show_default=False,
        ),
    ] = None,
):
    """
    Add DNS record to zPod
    """
    print(
        f"Adding dns record for [magenta]{ip or host_id}={hostname}[/magenta] "
        f"to zPod [magenta]{zpod_name}[/magenta]"
    )

    z: ZpodClient = ZpodClient()
    z.zpods_dns_add.sync(
        id=f"name={zpod_name}",
        body=ZpodDnsCreate(
            hostname=hostname,
            ip=ip,
            host_id=host_id,
        ),
    )
    zpod_dns_list(zpod_name)


@app.command(name="update", no_args_is_help=True)
@unexpected_status_handler
def zpod_dns_update(
    zpod_name: Annotated[
        str,
        typer.Argument(
            help="zPod name",
            show_default=False,
        ),
    ],
    hostname: Annotated[
        str,
        typer.Option(
            "--hostname",
            help="Hostname",
            show_default=False,
        ),
    ],
    ip: Annotated[
        str,
        typer.Option(
            "--ip",
            help="IP Address",
            show_default=False,
        ),
    ],
    newhostname: Annotated[
        str,
        typer.Option(
            "--newhostname",
            help="New Hostname",
            show_default=False,
        ),
    ] = None,
    newip: Annotated[
        str,
        typer.Option(
            "--newip",
            help="New IP Address",
            show_default=False,
        ),
    ] = None,
    newhost_id: Annotated[
        int,
        typer.Option(
            "--newhost-id",
            help="New Host ID",
            show_default=False,
        ),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option(
            "-y",
            "--yes",
            help="Automatic yes to prompts.",
            show_default=False,
        ),
    ] = False,
):
    """
    Update DNS record on zPod
    """

    if not newip and not newhost_id and not newhostname:
        exit_with_error("Must provide newip/newhost-id or newhostname or both")

    # Default values to original values if not provided
    if not newhostname:
        newhostname = hostname
    if not newip and not newhost_id:
        newip = ip

    if not yes:
        confirm(
            "Are you sure you want to update the dns record "
            f"[magenta]{ip}={hostname}[/magenta] to "
            f"[magenta]{newip or newhost_id}={newhostname}[/magenta] "
            f"on [magenta]{zpod_name}[/magenta]?",
        )

    print(
        f"Updating dns record [magenta]{ip}={hostname}[/magenta] to "
        f"[magenta]{newip or newhost_id}={newhostname}[/magenta] "
        f"on zPod [magenta]{zpod_name}[/magenta]"
    )

    z: ZpodClient = ZpodClient()
    z.zpods_dns_update.sync(
        id=f"name={zpod_name}",
        ip=ip,
        hostname=hostname,
        body=ZpodDnsUpdate(
            ip=newip,
            hostname=newhostname,
            host_id=newhost_id,
        ),
    )
    zpod_dns_list(zpod_name)


@app.command(name="remove", no_args_is_help=True)
@unexpected_status_handler
def zpod_dns_remove(
    zpod_name: Annotated[
        str,
        typer.Argument(
            help="zPod name",
            show_default=False,
        ),
    ],
    ip: Annotated[
        str,
        typer.Option(
            "--ip",
            help="IP Address",
            show_default=False,
        ),
    ],
    hostname: Annotated[
        str,
        typer.Option(
            "--hostname",
            help="Hostname",
            show_default=False,
        ),
    ],
    yes: Annotated[
        bool,
        typer.Option(
            "-y",
            "--yes",
            help="Automatic yes to prompts.",
            show_default=False,
        ),
    ] = False,
):
    """
    Remove DNS record from zPod
    """
    if not yes:
        confirm(
            "Are you sure you want to remove dns record "
            f"[magenta]{ip}={hostname}[/magenta] on [magenta]{zpod_name}[/magenta]?",
        )

    print(
        f"Removing dns record [magenta]{ip}={hostname}[/magenta] "
        f"on zPod [magenta]{zpod_name}[/magenta]"
    )

    z: ZpodClient = ZpodClient()
    z.zpods_dns_remove.sync(
        id=f"name={zpod_name}",
        ip=ip,
        hostname=hostname,
    )
    zpod_dns_list(zpod_name)


if __name__ == "__main__":
    app()
