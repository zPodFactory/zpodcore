from typing import List, Optional

import typer
from rich import print
from rich.table import Table
from typing_extensions import Annotated

from zpodcli.lib.utils import console_print, exit_with_error
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler
from zpodsdk.models.endpoint_permission import EndpointPermission
from zpodsdk.models.endpoint_permission_group_add_remove import (
    EndpointPermissionGroupAddRemove,
)
from zpodsdk.models.endpoint_permission_user_add_remove import (
    EndpointPermissionUserAddRemove,
)
from zpodsdk.models.endpoint_permission_view import EndpointPermissionView
from zpodsdk.models.endpoint_view import EndpointView

app = typer.Typer(
    help="Endpoint Permissions",
    no_args_is_help=True,
)


def generate_table(
    z: ZpodClient,
    endpoint: EndpointView,
):
    endpoint_permissions: List[EndpointPermissionView] = (
        z.endpoints_permissions_get_all.sync(endpoint.id)
    )

    title = "Endpoint Permission List"

    table = Table(
        title=title,
        min_width=60,
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
    console_print(title, table)


@app.command(name="list", no_args_is_help=True)
@unexpected_status_handler
def endpoint_permission_list(
    endpoint_name: Annotated[
        str,
        typer.Argument(
            help="Endpoint name",
            show_default=False,
        ),
    ],
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
    endpoint_name: Annotated[
        str,
        typer.Argument(
            help="Endpoint name",
            show_default=False,
        ),
    ],
    username: Annotated[
        Optional[str],
        typer.Option(
            "--username",
            "-u",
            help="Username to add",
            show_default=False,
        ),
    ] = None,
    groupname: Annotated[
        Optional[str],
        typer.Option(
            "--group",
            "-g",
            help="Group to add",
            show_default=False,
        ),
    ] = None,
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
    endpoint_name: Annotated[
        str,
        typer.Argument(
            help="Endpoint name",
            show_default=False,
        ),
    ],
    username: Annotated[
        Optional[str],
        typer.Option(
            "--username",
            "-u",
            help="Username to remove",
            show_default=False,
        ),
    ] = None,
    groupname: Annotated[
        Optional[str],
        typer.Option(
            "--group",
            "-g",
            help="Group to remove",
            show_default=False,
        ),
    ] = None,
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
