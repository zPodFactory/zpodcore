import typer
from rich import print
from zpod.models.permission_group_user_add import PermissionGroupUserAdd

from zpodcli.lib import utils, zpod_client

app = typer.Typer(help="Manage Permission Group Users")


@app.command(name="add", no_args_is_help=True)
def permission_group_user_add(
    name: str = typer.Option(..., "--name", "-n"),
    username: str = typer.Option(
        ...,
        "-u",
        help="username to add",
    ),
):
    """
    Add User to Permission Group
    """

    z: zpod_client.ZpodClient = zpod_client.ZpodClient()
    if not (user := z.users_get.sync(id=f"username={username}")):
        print(f"User not found: {username}")
        raise typer.Exit()

    result = z.permission_groups_users_add.sync_detailed(
        id=f"name={name}", json_body=PermissionGroupUserAdd(user_id=user.id)
    )

    if result.status_code == 201:
        print(f"User: {username} added.")
    else:
        utils.handle_response(result)


@app.command(name="remove", no_args_is_help=True)
def permission_group_user_remove(
    name: str = typer.Option(..., "--name", "-n"),
    username: str = typer.Option(
        ...,
        "-u",
        help="username to remove",
    ),
):
    """
    Remove User from Permission Group
    """
    z: zpod_client.ZpodClient = zpod_client.ZpodClient()
    if not (user := z.users_get.sync(id=f"username={username}")):
        print(f"User not found: {username}")
        raise typer.Exit()
    result = z.permission_groups_users_delete.sync_detailed(
        id=f"name={name}",
        user_id=user.id,
    )

    if result.status_code == 204:
        print(f"User: {username} removed.")
    else:
        utils.handle_response(result)
