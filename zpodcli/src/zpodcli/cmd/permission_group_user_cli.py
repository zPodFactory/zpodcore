import typer
from rich import print
from typing_extensions import Annotated

from zpodcli.lib.utils import exit_with_error
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler
from zpodsdk.models.permission_group_user_add import PermissionGroupUserAdd

app = typer.Typer(help="Manage Permission Group Users")


@app.command(name="add", no_args_is_help=True)
@unexpected_status_handler
def permission_group_user_add(
    group_name: Annotated[
        str,
        typer.Argument(
            help="Group name",
            show_default=False,
        ),
    ],
    username: Annotated[
        str,
        typer.Option(
            "--username",
            "-u",
            help="Username to add",
            show_default=False,
        ),
    ],
):
    """
    Add User to Permission Group
    """

    z: ZpodClient = ZpodClient()
    if not (user := z.users_get.sync(id=f"username={username}")):
        exit_with_error(f"User not found: {username}")

    z.permission_groups_users_add.sync(
        id=f"name={group_name}",
        body=PermissionGroupUserAdd(user_id=user.id),
    )
    print(f"User: {username} added.")


@app.command(name="remove", no_args_is_help=True)
@unexpected_status_handler
def permission_group_user_remove(
    group_name: Annotated[
        str,
        typer.Argument(
            help="Group name",
            show_default=False,
        ),
    ],
    username: Annotated[
        str,
        typer.Option(
            "--username",
            "-u",
            help="Username to remove",
            show_default=False,
        ),
    ],
):
    """
    Remove User from Permission Group
    """
    z: ZpodClient = ZpodClient()
    if not (user := z.users_get.sync(id=f"username={username}")):
        exit_with_error(f"User not found: {username}")
    z.permission_groups_users_delete.sync(
        id=f"name={group_name}",
        user_id=user.id,
    )
    print(f"User: {username} removed.")
