import typer
from rich import print
from rich.table import Table
from typing_extensions import Annotated
from zpod.models.user_create import UserCreate
from zpod.models.user_update_admin import UserUpdateAdmin

from zpodcli.lib.utils import get_boolean_markdown
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler

app = typer.Typer(help="Manage Users")


def generate_table(users, all=False):
    table = Table(
        "Username",
        "Email",
        "Description",
        "Creation Date",
        "Last Connection",
        "Superadmin",
        title="User List",
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    if all:
        table.add_column("Status")

    for user in sorted(users, key=lambda c: c.username):
        lcd = (
            user.last_connection_date.strftime("%Y-%m-%d %H:%M:%S")
            if user.last_connection_date
            else ""
        )
        row = [
            user.username,
            f"[sky_blue2]{user.email}[/sky_blue2]",
            user.description,
            f"[tan]{user.creation_date.strftime('%Y-%m-%d %H:%M:%S')}[/tan]",
            f"[magenta]{lcd}[/magenta]",  # noqa: E501
            get_boolean_markdown(user.superadmin),
        ]
        if all:
            row.append(user.status)
        table.add_row(
            *row,
        )
    print(table)


@app.command(name="list")
@unexpected_status_handler
def user_list(
    all: Annotated[
        bool,
        typer.Option("--all", help="Show all Users"),
    ] = False,
):
    """
    List Users
    """
    z: ZpodClient = ZpodClient()
    users = z.users_get_all.sync(all_=all)
    generate_table(users, all=all)


@app.command(name="add", no_args_is_help=True)
@unexpected_status_handler
def user_add(
    username: Annotated[
        str,
        typer.Option("--username", "-u", help="Username"),
    ],
    email: Annotated[
        str,
        typer.Option("--email", "-e", help="Email"),
    ],
    description: Annotated[
        str,
        typer.Option("--description", "-d", help="Description"),
    ] = "",
    ssh_key: Annotated[
        str,
        typer.Option("--ssh_key", "-s", help="SSH Key"),
    ] = "",
    superadmin: Annotated[
        bool,
        typer.Option("--superadmin", help="Superadmin"),
    ] = False,
):
    """
    Add User
    """
    z: ZpodClient = ZpodClient()
    result = z.users_create.sync(
        body=UserCreate(
            username=username,
            email=email,
            description=description,
            ssh_key=ssh_key,
            superadmin=superadmin,
        )
    )

    print(
        f"User [magenta]{username}[/magenta] has been created.\n"
        f"Token: [tan]{result.api_token}[/tan]"
    )


@app.command(name="update", no_args_is_help=True)
@unexpected_status_handler
def user_update(
    username: Annotated[
        str,
        typer.Option("--username", "-u", help="Username"),
    ],
    description: Annotated[
        str,
        typer.Option("--description", "-d", help="Description"),
    ] = "",
    ssh_key: Annotated[
        str,
        typer.Option("--ssh_key", "-s", help="SSH Key"),
    ] = "",
    superadmin: Annotated[
        bool,
        typer.Option("--superadmin", help="Superadmin"),
    ] = False,
):
    """
    Update User
    """
    z: ZpodClient = ZpodClient()
    z.users_update.sync(
        id=f"username={username}",
        body=UserUpdateAdmin(
            description=description,
            ssh_key=ssh_key,
            superadmin=superadmin,
        ),
    )
    print(f"User [magenta]{username}[/magenta] has been updated.")


@app.command(name="enable", no_args_is_help=True)
@unexpected_status_handler
def user_enable(
    username: Annotated[
        str,
        typer.Option("--username", "-u", help="Username"),
    ],
):
    """
    Enable User
    """
    z: ZpodClient = ZpodClient()
    z.users_enable.sync(id=f"username={username}")
    print(f"User [magenta]{username}[/magenta] has been enabled.")


@app.command(name="disable", no_args_is_help=True)
@unexpected_status_handler
def user_disable(
    username: Annotated[
        str,
        typer.Option("--username", "-u", help="Username"),
    ],
):
    """
    Disable User
    """
    z: ZpodClient = ZpodClient()
    z.users_disable.sync(id=f"username={username}")
    print(f"User [magenta]{username}[/magenta] has been disabled.")


@app.command(name="reset_api_token", no_args_is_help=True)
@unexpected_status_handler
def user_reset_api_token(
    username: Annotated[
        str,
        typer.Option("--username", "-u", help="Username"),
    ],
):
    """
    Reset User api_token
    """
    z: ZpodClient = ZpodClient()
    result = z.users_reset_api_token.sync(id=f"username={username}")
    print(
        f"User [magenta]{username}[/magenta]'s api_token has been reset "
        f"to: [tan]{result.api_token}[/tan]"
    )
