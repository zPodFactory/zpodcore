from enum import Enum
from typing import List

import typer
from rich import print
from rich.console import Console
from rich.table import Table
from zpod.models.endpoint_permission_group_add_remove import (
    EndpointPermissionGroupAddRemove,
)
from zpod.models.endpoint_permission_user_add_remove import (
    EndpointPermissionUserAddRemove,
)
from zpod.models.endpoint_permission_view import EndpointPermissionView
from zpod.models.endpoint_view import EndpointView

from zpodcli.lib.utils import exit_with_error
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler


class EndpointPermission(str, Enum):
    USER = "USER"


app = typer.Typer(
    help="Manage zPods Endpoint Permissions",
    no_args_is_help=True,
)

console = Console()


def generate_table(
    z: ZpodClient,
    endpoint: EndpointView,
):
    endpoint_permissions: List[
        EndpointPermissionView
    ] = z.endpoints_permissions_get_all.sync(endpoint.id)

    title = f"{endpoint.name} Permissions"

    table = Table(
        title=title,
        min_width=25,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Users")
    table.add_column("Groups")

    for ip in endpoint_permissions:
        users = "\n".join(sorted(x.username for x in ip.users))
        groups = "\n".join(sorted(x.name for x in ip.permission_groups))
        table.add_row(
            f"[light_coral]{users}[/light_coral]",
            f"[cornflower_blue]{groups}[/cornflower_blue]",
        )
    console.print(table)


@app.command(name="list", no_args_is_help=True)
@unexpected_status_handler
def endpoint_permission_list(
    endpoint_name: str = typer.Option(..., "-e", help="endpoint name"),
):
    """
    List endpoint permission
    """

    z = ZpodClient()
    endpoint = z.endpoints_get.sync(id=f"name={endpoint_name}")
    generate_table(z, endpoint)


@app.command(name="add", no_args_is_help=True)
@unexpected_status_handler
def endpoint_permission_add(
    *,
    endpoint_name: str = typer.Option(
        ...,
        "-e",
        help="endpoint name",
    ),
    username: str = typer.Option(
        None,
        "-u",
        help="username to add",
    ),
    groupname: str = typer.Option(
        None,
        "-g",
        help="group to add",
    ),
):
    """
    Add permission to endpoint
    """
    print(f"Adding permission to endpoint {endpoint_name}")

    if not username and not groupname:
        exit_with_error("Must provide either username or groupname")
    if username and groupname:
        exit_with_error("Can not provide both username and groupname")

    z = ZpodClient()
    endpoint = z.endpoints_get.sync(id=f"name={endpoint_name}")
    if username:
        z.endpoints_permissions_users_add.sync(
            id=endpoint.id,
            permission=EndpointPermission.USER.value,
            body=EndpointPermissionUserAddRemove(username=username),
        )
    else:
        z.endpoints_permissions_groups_add.sync(
            id=endpoint.id,
            permission=EndpointPermission.USER.value,
            body=EndpointPermissionGroupAddRemove(groupname=groupname),
        )
    generate_table(z, endpoint)


@app.command(name="remove", no_args_is_help=True)
@unexpected_status_handler
def endpoint_permission_remove(
    *,
    endpoint_name: str = typer.Option(
        ...,
        "-e",
        help="endpoint name",
    ),
    username: str = typer.Option(
        None,
        "-u",
        help="username to remove",
    ),
    groupname: str = typer.Option(
        None,
        "-g",
        help="group to remove",
    ),
):
    """
    Remove permission from endpoint
    """
    print(f"Remove permission from endpoint {endpoint_name}")

    if not username and not groupname:
        exit_with_error("Must provide either username or groupname")
    if username and groupname:
        exit_with_error("Can not provide both username and groupname")

    z = ZpodClient()
    endpoint = z.endpoints_get.sync(id=f"name={endpoint_name}")
    if username:
        z.endpoints_permissions_users_remove.sync(
            id=endpoint.id,
            permission=EndpointPermission.USER.value,
            body=EndpointPermissionUserAddRemove(username=username),
        )
    else:
        z.endpoints_permissions_groups_remove.sync(
            id=endpoint.id,
            permission=EndpointPermission.USER.value,
            body=EndpointPermissionGroupAddRemove(groupname=groupname),
        )
    generate_table(z, endpoint)
