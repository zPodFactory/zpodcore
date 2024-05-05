from enum import Enum
from typing import List, Optional

import typer
from rich import print
from rich.table import Table
from typing_extensions import Annotated

from zpodcli.lib.utils import console_print, exit_with_error
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler
from zpodsdk.models.zpod_permission_group_add_remove import (
    ZpodPermissionGroupAddRemove,
)
from zpodsdk.models.zpod_permission_user_add_remove import (
    ZpodPermissionUserAddRemove,
)
from zpodsdk.models.zpod_permission_view import ZpodPermissionView
from zpodsdk.models.zpod_view import ZpodView


class ZpodPermission(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    USER = "USER"


app = typer.Typer(
    help="Manage zPod Permissions",
    no_args_is_help=True,
)


def generate_table(
    z: ZpodClient,
    zp: ZpodView,
):
    zpod_permissions: List[ZpodPermissionView] = z.zpods_permissions_get_all.sync(zp.id)

    title = f"zPod Permission list {zp.name}"

    table = Table(
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Permission")
    table.add_column("Users")
    table.add_column("Groups")

    sorted_zpod_permissions = [
        zp for eip in ZpodPermission for zp in zpod_permissions if zp.permission == eip
    ]

    for zp in sorted_zpod_permissions:
        users = "\n".join(sorted(x.username for x in zp.users))
        groups = "\n".join(sorted(x.name for x in zp.permission_groups))
        table.add_row(
            f"[yellow3]{zp.permission}[/yellow3]",
            f"[light_coral]{users}[/light_coral]",
            f"[cornflower_blue]{groups}[/cornflower_blue]",
        )
    console_print(title, table)


@app.command(name="list", no_args_is_help=True)
@unexpected_status_handler
def zpod_permission_list(
    zpod_name: Annotated[
        str,
        typer.Argument(
            help="zPod name",
            show_default=False,
        ),
    ],
):
    """
    List zPod Permissions
    """

    z = ZpodClient()
    zpod = z.zpods_get.sync(id=f"name={zpod_name}")

    generate_table(z, zpod)


@app.command(name="add", no_args_is_help=True)
@unexpected_status_handler
def zpod_permission_add(
    *,
    zpod_name: Annotated[
        str,
        typer.Argument(
            help="zPod name",
            show_default=False,
        ),
    ],
    permission: Annotated[
        ZpodPermission,
        typer.Option(
            "--permission",
            "-p",
            show_default=False,
            help="Permission",
            case_sensitive=False,
        ),
    ],
    username: Annotated[
        Optional[str],
        typer.Option(
            "--username",
            "-u",
            show_default=False,
            help="Username to add",
        ),
    ] = None,
    groupname: Annotated[
        Optional[str],
        typer.Option(
            "--group",
            "-g",
            show_default=False,
            help="Group to add",
        ),
    ] = None,
):
    """
    Add Permission to zPod
    """
    print(f"Adding permission to zPod: {zpod_name}")

    if not username and not groupname:
        exit_with_error("Must provide either username or groupname")
    if username and groupname:
        exit_with_error("Can not provide both username and groupname")

    z = ZpodClient()
    zpod = z.zpods_get.sync(id=f"name={zpod_name}")
    if username:
        z.zpods_permissions_users_add.sync(
            id=zpod.id,
            permission=permission.value,
            body=ZpodPermissionUserAddRemove(username=username),
        )
    if groupname:
        z.zpods_permissions_groups_add.sync(
            id=zpod.id,
            permission=permission.value,
            body=ZpodPermissionGroupAddRemove(groupname=groupname),
        )
    generate_table(z, zpod)


@app.command(name="remove", no_args_is_help=True)
@unexpected_status_handler
def zpod_permission_remove(
    *,
    zpod_name: Annotated[
        str,
        typer.Argument(
            help="zPod name",
            show_default=False,
        ),
    ],
    permission: Annotated[
        ZpodPermission,
        typer.Option(
            "--permission",
            "-p",
            show_default=False,
            help="permission",
            case_sensitive=False,
        ),
    ],
    username: Annotated[
        Optional[str],
        typer.Option(
            "--username",
            "-u",
            show_default=False,
            help="username to remove",
        ),
    ] = None,
    groupname: Annotated[
        Optional[str],
        typer.Option(
            "--group",
            "-g",
            show_default=False,
            help="group to remove",
        ),
    ] = None,
):
    """
    Remove Permission from zPod
    """
    print(f"Remove permission from zPod: {zpod_name}")

    if not username and not groupname:
        exit_with_error("Must provide either username or groupname")
    if username and groupname:
        exit_with_error("Can not provide both username and groupname")

    z = ZpodClient()
    zpod = z.zpods_get.sync(id=f"name={zpod_name}")
    if username:
        z.zpods_permissions_users_remove.sync(
            id=zpod.id,
            permission=permission.value,
            body=ZpodPermissionUserAddRemove(username=username),
        )
    if groupname:
        z.zpods_permissions_groups_remove.sync(
            id=zpod.id,
            permission=permission.value,
            body=ZpodPermissionGroupAddRemove(groupname=groupname),
        )
    generate_table(z, zpod)
