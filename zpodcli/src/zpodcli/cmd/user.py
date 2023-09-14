from http import HTTPStatus

import typer
from rich import print
from rich.table import Table
from zpod.models.user_create import UserCreate
from zpod.models.user_update_admin import UserUpdateAdmin

from zpodcli.lib import utils, zpod_client
from zpodcli.lib.utils import get_boolean_markdown

app = typer.Typer(help="Manage users")


def generate_table(users, all=False):
    if users.status_code == HTTPStatus.OK:
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

        for user in sorted(users.parsed, key=lambda c: c.username):
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
    else:
        utils.handle_response(users.content)


@app.command(name="list")
def user_list(
    all: bool = typer.Option(
        False,
        "--all",
        help="Show all Users",
    ),
):
    """
    List users
    """
    z = zpod_client.ZpodClient()
    users = z.users_get_all.sync_detailed(all_=all)
    generate_table(users, all=all)


@app.command(name="add", no_args_is_help=True)
def user_add(
    username: str = typer.Option(
        ...,
        "--username",
        "-u",
        help="Username",
    ),
    email: str = typer.Option(
        ...,
        "--email",
        "-e",
        help="Email",
    ),
    description: str = typer.Option(
        "",
        "--description",
        "-d",
        help="Description",
    ),
    ssh_key: str = typer.Option(
        "",
        "--ssh_key",
        "-s",
        help="SSH Key",
    ),
    superadmin: bool = typer.Option(
        False,
        "--superadmin",
        help="Superadmin",
    ),
):
    """
    Add user
    """
    z: zpod_client.ZpodClient = zpod_client.ZpodClient()

    result = z.users_create.sync_detailed(
        json_body=UserCreate(
            username=username,
            email=email,
            description=description,
            ssh_key=ssh_key,
            superadmin=superadmin,
        )
    )

    if result.status_code == 201:
        print(
            f"User [magenta]{username}[/magenta] has been created.\n"
            f"Token: [tan]{result.parsed.api_token}[/tan]"
        )
    else:
        utils.handle_response(result)


@app.command(name="update", no_args_is_help=True)
def user_update(
    username: str = typer.Option(
        ...,
        "--username",
        "-u",
        help="Username",
    ),
    description: str = typer.Option(
        "",
        "--description",
        "-d",
        help="Description",
    ),
    ssh_key: str = typer.Option(
        "",
        "--ssh_key",
        "-s",
        help="SSH Key",
    ),
    superadmin: bool = typer.Option(
        False,
        "--superadmin",
        help="Superadmin",
    ),
):
    """
    Update user
    """
    z: zpod_client.ZpodClient = zpod_client.ZpodClient()

    result = z.users_update.sync_detailed(
        id=f"username={username}",
        json_body=UserUpdateAdmin(
            description=description,
            ssh_key=ssh_key,
            superadmin=superadmin,
        ),
    )

    if result.status_code == 201:
        print(f"User [magenta]{username}[/magenta] has been updated.")
    else:
        utils.handle_response(result)


@app.command(name="enable", no_args_is_help=True)
def user_enable(
    username: str = typer.Option(
        ...,
        "--username",
        "-u",
        help="Username",
    ),
):
    """
    Enable user
    """
    z = zpod_client.ZpodClient()
    result = z.users_enable.sync_detailed(id=f"username={username}")
    if result.status_code == 201:
        print(f"User [magenta]{username}[/magenta] has been enabled.")
    else:
        utils.handle_response(result)


@app.command(name="disable", no_args_is_help=True)
def user_disable(
    username: str = typer.Option(
        ...,
        "--username",
        "-u",
        help="Username",
    ),
):
    """
    Disable user
    """
    z = zpod_client.ZpodClient()
    result = z.users_disable.sync_detailed(id=f"username={username}")
    if result.status_code == 201:
        print(f"User [magenta]{username}[/magenta] has been disabled.")
    else:
        utils.handle_response(result)


@app.command(name="reset_api_token", no_args_is_help=True)
def user_reset_api_token(
    username: str = typer.Option(
        ...,
        "--username",
        "-u",
        help="Username",
    ),
):
    """
    Reset user api_token
    """
    z = zpod_client.ZpodClient()
    result = z.users_reset_api_token.sync_detailed(id=f"username={username}")
    if result.status_code == 201:
        print(
            f"User [magenta]{username}[/magenta]'s api_token has been reset "
            f"to: [tan]{result.parsed.api_token}[/tan]"
        )
    else:
        utils.handle_response(result)
