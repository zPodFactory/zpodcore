from typing import Optional

import typer
from rich import print
from rich.table import Table
from typing_extensions import Annotated

from zpodcli.lib.utils import (
    JsonOption,
    NoColorOption,
    console_print,
    exit_with_error,
    get_boolean_markdown,
    json_print,
)
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler
from zpodsdk.models.user_create import UserCreate
from zpodsdk.models.user_update_admin import UserUpdateAdmin
from zpodsdk.types import UNSET

app = typer.Typer(help="Manage Users")


def generate_table(users, all_=False):
    title = "User List"
    table = Table(
        "Username",
        "Email",
        "Description",
        "Creation Date",
        "Last Connection",
        "Superadmin",
        "API Token",
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    if all_:
        table.add_column("Status")

    for user in sorted(users, key=lambda c: c.username):
        lcd = (
            user.last_connection_date.strftime("%Y-%m-%d %H:%M:%S")
            if user.last_connection_date
            else ""
        )
        # Only visible for superadmins and for a user's own row (see
        # GET /users masking in zpodapi); other rows show a placeholder.
        api_token = (
            f"[grey58]{user.api_token}[/grey58]" if user.api_token else "[dim]—[/dim]"
        )
        row = [
            user.username,
            f"[sky_blue2]{user.email}[/sky_blue2]",
            user.description,
            f"[tan]{user.creation_date.strftime('%Y-%m-%d %H:%M:%S')}[/tan]",
            f"[magenta]{lcd}[/magenta]",  # noqa: E501
            get_boolean_markdown(user.superadmin),
            api_token,
        ]
        if all_:
            row.append(user.status)
        table.add_row(
            *row,
        )

    console_print(title, table)


@app.command(name="list")
@unexpected_status_handler
def user_list(
    all_: Annotated[
        bool,
        typer.Option(
            "--all",
            "-a",
            help="Show all Users",
        ),
    ] = False,
    json_: JsonOption = False,
    no_color: NoColorOption = False,
):
    """
    List Users
    """
    z: ZpodClient = ZpodClient()
    users = z.users_get_all.sync(all_=all_)
    if json_:
        json_print([user.to_dict() for user in users])
    else:
        generate_table(users, all_=all_)


@app.command(name="add", no_args_is_help=True)
@unexpected_status_handler
def user_add(
    username: Annotated[
        str,
        typer.Argument(
            help="Username",
            show_default=False,
        ),
    ],
    email: Annotated[
        str,
        typer.Option(
            "--email",
            "-e",
            help="Email",
            show_default=False,
        ),
    ],
    description: Annotated[
        str,
        typer.Option(
            "--description",
            "-d",
            help="Description",
        ),
    ] = "",
    ssh_key: Annotated[
        str,
        typer.Option(
            "--ssh-key",
            "-s",
            help="SSH Key",
        ),
    ] = "",
    superadmin: Annotated[
        bool,
        typer.Option(
            "--superadmin",
            help="Superadmin",
        ),
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
        typer.Argument(
            help="Username",
            show_default=False,
        ),
    ],
    email: Annotated[
        Optional[str],
        typer.Option(
            "--email",
            "-e",
            help="Email",
            show_default=False,
        ),
    ] = None,
    description: Annotated[
        Optional[str],
        typer.Option(
            "--description",
            "-d",
            help="Description",
            show_default=False,
        ),
    ] = None,
    ssh_key: Annotated[
        Optional[str],
        typer.Option(
            "--ssh-key",
            "-s",
            help="SSH Key",
            show_default=False,
        ),
    ] = None,
    superadmin: Annotated[
        Optional[bool],
        typer.Option(
            "--superadmin/--no-superadmin",
            help="Grant or revoke superadmin",
            show_default=False,
        ),
    ] = None,
):
    """
    Update User (only the provided fields are changed)
    """
    if all(value is None for value in (email, description, ssh_key, superadmin)):
        exit_with_error("No changes specified")

    # Fields left at None are sent as UNSET so the API keeps their current
    # value instead of overwriting them with an empty default.
    z: ZpodClient = ZpodClient()
    z.users_update.sync(
        id=f"username={username}",
        body=UserUpdateAdmin(
            email=UNSET if email is None else email,
            description=UNSET if description is None else description,
            ssh_key=UNSET if ssh_key is None else ssh_key,
            superadmin=UNSET if superadmin is None else superadmin,
        ),
    )
    print(f"User [magenta]{username}[/magenta] has been updated.")


@app.command(name="delete", no_args_is_help=True)
@unexpected_status_handler
def user_delete(
    username: Annotated[
        str,
        typer.Argument(
            help="Username",
            show_default=False,
        ),
    ],
):
    """
    Delete User
    """
    z: ZpodClient = ZpodClient()
    z.users_delete.sync(id=f"username={username}")
    print(f"User [magenta]{username}[/magenta] has been deleted.")


@app.command(name="enable", no_args_is_help=True)
@unexpected_status_handler
def user_enable(
    username: Annotated[
        str,
        typer.Argument(
            help="Username",
            show_default=False,
        ),
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
        typer.Argument(
            help="Username",
            show_default=False,
        ),
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
        typer.Argument(
            help="Username",
            show_default=False,
        ),
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
