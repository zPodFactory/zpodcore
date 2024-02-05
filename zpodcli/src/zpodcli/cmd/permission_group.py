import typer
from rich import print
from rich.table import Table
from typing_extensions import Annotated
from zpod.models.permission_group_create import PermissionGroupCreate
from zpod.models.permission_group_update import PermissionGroupUpdate
from zpod.models.permission_group_view import PermissionGroupView

from zpodcli.cmd import permission_group_user
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler

app = typer.Typer(help="Manage Permission Groups")
app.add_typer(permission_group_user.app, name="user", no_args_is_help=True)


def generate_table(
    permission_groups: list[PermissionGroupView],
):
    table = Table(
        "Permission Group",
        "Usernames",
        title="Permission Groups",
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    for permission_group in permission_groups:
        usernames = "\n".join(sorted(x.username for x in permission_group.users))
        table.add_row(
            f"[tan]{permission_group.name}[/tan]",
            f"[light_coral]{usernames}[/light_coral]",
        )
    print(table)


@app.command(name="list")
@unexpected_status_handler
def permission_group_list():
    """
    List Permission Groups
    """
    z: ZpodClient = ZpodClient()
    result = z.permission_groups_get_all.sync()
    generate_table(result)


@app.command(name="create", no_args_is_help=True)
@unexpected_status_handler
def permission_group_create(
    name: Annotated[
        str,
        typer.Option("--name", "-n"),
    ],
):
    """
    Create Permission Group
    """

    z: ZpodClient = ZpodClient()
    z.permission_groups_create.sync(
        body=PermissionGroupCreate(
            name=name,
        )
    )
    print(f"Permission Group [magenta]{name}[/magenta] has been created.")


@app.command(name="update", no_args_is_help=True)
@unexpected_status_handler
def permission_group_update(
    name: Annotated[
        str,
        typer.Option("--name", "-n"),
    ],
    newname: Annotated[
        str,
        typer.Option("--newname"),
    ],
):
    """
    Update Permission Group
    """
    if newname == name:
        print("New name is the same as the old name")
        raise typer.Exit()

    z: ZpodClient = ZpodClient()
    z.permission_groups_update.sync(
        id=f"name={name}",
        body=PermissionGroupUpdate(name=newname),
    )
    print(
        f"Permission Group [magenta]{name}[/magenta] has been "
        f"renamed to [magenta]{newname}[/magenta]."
    )


@app.command(name="delete", no_args_is_help=True)
@unexpected_status_handler
def permission_group_delete(
    name: Annotated[
        str,
        typer.Option("--name", "-n"),
    ],
):
    """
    Delete Permission Group
    """
    z: ZpodClient = ZpodClient()

    z.permission_groups_delete.sync(
        id=f"name={name}",
    )
    print(f"Permission Group [magenta]{name}[/magenta] has been deleted.")
