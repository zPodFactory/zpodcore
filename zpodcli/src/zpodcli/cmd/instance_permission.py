from enum import Enum
from typing import List, Optional

import typer
from rich import print
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated
from zpod.models.instance_permission_group_add_remove import (
    InstancePermissionGroupAddRemove,
)
from zpod.models.instance_permission_user_add_remove import (
    InstancePermissionUserAddRemove,
)
from zpod.models.instance_permission_view import InstancePermissionView
from zpod.models.instance_view import InstanceView

from zpodcli.lib.utils import exit_with_error
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler


class InstancePermission(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    USER = "USER"


app = typer.Typer(
    help="Manage zPods Instance Permissions",
    no_args_is_help=True,
)

console = Console()


def generate_table(
    z: ZpodClient,
    instance: InstanceView,
):
    instance_permissions: List[
        InstancePermissionView
    ] = z.instances_permissions_get_all.sync(instance.id)

    title = f"{instance.name} Permissions"

    table = Table(
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Permission")
    table.add_column("Users")
    table.add_column("Groups")

    sorted_instance_permissions = [
        ip
        for eip in InstancePermission
        for ip in instance_permissions
        if ip.permission == eip
    ]

    for ip in sorted_instance_permissions:
        users = "\n".join(sorted(x.username for x in ip.users))
        groups = "\n".join(sorted(x.name for x in ip.permission_groups))
        table.add_row(
            f"[yellow3]{ip.permission}[/yellow3]",
            f"[light_coral]{users}[/light_coral]",
            f"[cornflower_blue]{groups}[/cornflower_blue]",
        )
    console.print(table)


@app.command(name="list", no_args_is_help=True)
@unexpected_status_handler
def instance_permission_list(
    instance_name: Annotated[
        str,
        typer.Option("-i", help="instance name"),
    ],
):
    """
    List instance permission
    """

    z = ZpodClient()
    instance = z.instances_get.sync(id=f"name={instance_name}")

    generate_table(z, instance)


@app.command(name="add", no_args_is_help=True)
@unexpected_status_handler
def instance_permission_add(
    *,
    instance_name: Annotated[
        str,
        typer.Option("-i", help="instance name"),
    ],
    permission: Annotated[
        InstancePermission,
        typer.Option("-p", help="permission", case_sensitive=False),
    ],
    username: Annotated[
        Optional[str],
        typer.Option("-u", help="username to add"),
    ] = None,
    groupname: Annotated[
        Optional[str],
        typer.Option("-g", help="group to add"),
    ] = None,
):
    """
    Add permission to instance
    """
    print(f"Adding permission to instance {instance_name}")

    if not username and not groupname:
        exit_with_error("Must provide either username or groupname")
    if username and groupname:
        exit_with_error("Can not provide both username and groupname")

    z = ZpodClient()
    instance = z.instances_get.sync(id=f"name={instance_name}")
    if username:
        z.instances_permissions_users_add.sync(
            id=instance.id,
            permission=permission.value,
            body=InstancePermissionUserAddRemove(username=username),
        )
    if groupname:
        z.instances_permissions_groups_add.sync(
            id=instance.id,
            permission=permission.value,
            body=InstancePermissionGroupAddRemove(groupname=groupname),
        )
    generate_table(z, instance)


@app.command(name="remove", no_args_is_help=True)
@unexpected_status_handler
def instance_permission_remove(
    *,
    instance_name: Annotated[
        str,
        typer.Option("-i", help="instance name"),
    ],
    permission: Annotated[
        InstancePermission,
        typer.Option("-p", help="permission", case_sensitive=False),
    ],
    username: Annotated[
        Optional[str],
        typer.Option("-u", help="username to remove"),
    ] = None,
    groupname: Annotated[
        Optional[str],
        typer.Option("-g", help="group to remove"),
    ] = None,
):
    """
    Remove permission from instance
    """
    print(f"Remove permission from instance {instance_name}")

    if not username and not groupname:
        exit_with_error("Must provide either username or groupname")
    if username and groupname:
        exit_with_error("Can not provide both username and groupname")

    z = ZpodClient()
    instance = z.instances_get.sync(id=f"name={instance_name}")
    if username:
        z.instances_permissions_users_remove.sync(
            id=instance.id,
            permission=permission.value,
            body=InstancePermissionUserAddRemove(username=username),
        )
    if groupname:
        z.instances_permissions_groups_remove.sync(
            id=instance.id,
            permission=permission.value,
            body=InstancePermissionGroupAddRemove(groupname=groupname),
        )
    generate_table(z, instance)
