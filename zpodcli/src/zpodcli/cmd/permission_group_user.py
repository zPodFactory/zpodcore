import typer
from rich import print
from typing_extensions import Annotated
from zpod.models.permission_group_user_add import PermissionGroupUserAdd

from zpodcli.lib.utils import exit_with_error
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler

app = typer.Typer(help="Manage Permission Group Users")


@app.command(name="add", no_args_is_help=True)
@unexpected_status_handler
def permission_group_user_add(
    name: Annotated[
        str,
        typer.Option("--name", "-n"),
    ],
    username: Annotated[
        str,
        typer.Option("-u", help="username to add"),
    ],
):
    """
    Add User to Permission Group
    """

    z: ZpodClient = ZpodClient()
    if not (user := z.users_get.sync(id=f"username={username}")):
        exit_with_error(f"User not found: {username}")

    z.permission_groups_users_add.sync(
        id=f"name={name}",
        body=PermissionGroupUserAdd(user_id=user.id),
    )
    print(f"User: {username} added.")


@app.command(name="remove", no_args_is_help=True)
@unexpected_status_handler
def permission_group_user_remove(
    name: Annotated[
        str,
        typer.Option("--name", "-n"),
    ],
    username: Annotated[
        str,
        typer.Option("-u", help="username to remove"),
    ],
):
    """
    Remove User from Permission Group
    """
    z: ZpodClient = ZpodClient()
    if not (user := z.users_get.sync(id=f"username={username}")):
        exit_with_error(f"User not found: {username}")
    z.permission_groups_users_delete.sync(
        id=f"name={name}",
        user_id=user.id,
    )
    print(f"User: {username} removed.")
