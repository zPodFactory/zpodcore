from http import HTTPStatus

import typer
from rich import print
from rich.table import Table

from zpodcli.lib import utils, zpod_client
from zpodcli.lib.utils import get_boolean_markdown

app = typer.Typer(help="Manage users")


@app.command(name="list")
def user_list():
    """
    List users
    """
    z = zpod_client.ZpodClient()
    users = z.users_get_all.sync_detailed()
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

        for user in users.parsed:
            table.add_row(
                f"{user.username}",
                f"[sky_blue2]{user.email}[/sky_blue2]",
                user.description,
                f"[tan]{user.creation_date.strftime('%Y-%m-%d %H:%M:%S')}[/tan]",
                f"[magenta]{user.last_connection_date.strftime('%Y-%m-%d %H:%M:%S')}[/magenta]",
                get_boolean_markdown(user.superadmin),
            )
        print(table)
    else:
        utils.handle_response(users.content)
