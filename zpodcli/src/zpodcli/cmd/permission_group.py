import typer
from rich import print
from rich.table import Table
from zpod.models.permission_group_create import PermissionGroupCreate
from zpod.models.permission_group_update import PermissionGroupUpdate
from zpod.models.permission_group_view import PermissionGroupView

from zpodcli.cmd import permission_group_user
from zpodcli.lib import utils, zpod_client

app = typer.Typer(help="Manage Permission Groups")
app.add_typer(permission_group_user.app, name="user", no_args_is_help=True)


def generate_table(
    permission_groups: list[PermissionGroupView],
):
    table = Table(
        "Permission Group",
        "Users",
        title="Permission Groups",
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    for permission_group in permission_groups:
        users = "\n".join(sorted([x.username for x in permission_group.users]))
        table.add_row(
            f"[tan]{permission_group.name}[/tan]",
            f"[light_coral]{users}[/light_coral]",
        )
    print(table)


@app.command(name="list")
def permission_group_list():
    """
    List Permission Groups
    """
    z = zpod_client.ZpodClient()
    result = z.permission_groups_get_all.sync_detailed()

    if result.status_code == 200:
        generate_table(result.parsed)
    else:
        utils.handle_response(result)


@app.command(name="create", no_args_is_help=True)
def permission_group_create(
    name: str = typer.Option(..., "--name", "-n"),
):
    """
    Create Permission Group
    """

    z: zpod_client.ZpodClient = zpod_client.ZpodClient()
    result = z.permission_groups_create.sync_detailed(
        json_body=PermissionGroupCreate(
            name=name,
        )
    )

    if result.status_code == 201:
        print(f"Permission Group [magenta]{name}[/magenta] has been created.")
    else:
        utils.handle_response(result)


@app.command(name="update", no_args_is_help=True)
def permission_group_update(
    name: str = typer.Option(..., "--name", "-n"),
    newname: str = typer.Option(..., "--newname"),
):
    """
    Update Permission Group
    """
    if newname == name:
        print("New name is the same as the old name")
        raise typer.Exit()

    z = zpod_client.ZpodClient()
    result = z.permission_groups_update.sync_detailed(
        id=f"name={name}",
        json_body=PermissionGroupUpdate(name=newname),
    )
    if result.status_code == 204:
        print(
            f"Permission Group [magenta]{name}[/magenta] has been "
            f"renamed to [magenta]{newname}[/magenta]."
        )
    else:
        utils.handle_response(result)


@app.command(name="delete", no_args_is_help=True)
def permission_group_delete(
    name: str = typer.Option(..., "--name", "-n"),
):
    """
    Delete Permission Group
    """
    z = zpod_client.ZpodClient()
    result = z.permission_groups_delete.sync_detailed(
        id=f"name={name}",
    )
    if result.status_code == 204:
        print(f"Permission Group [magenta]{name}[/magenta] has been deleted.")
    else:
        utils.handle_response(result)
