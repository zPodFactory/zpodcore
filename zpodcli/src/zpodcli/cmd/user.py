import typer
from rich import print
from rich.console import Console
from rich.table import Table

from zpodcli.lib import zpod_client
from zpodcli.lib.callback import isauthenticated

app = typer.Typer(help="Manage users", callback=isauthenticated)


@app.command()
def list():
    """
    List users
    """
    print("Listing users...")

    z = zpod_client.ZpodClient()

    users = z.users_get_all.sync()

    print("Server UserView list")
    print(users)

    print("")
    print("[yellow][blink]Rich Table nice view ;-)[/blink][/yellow]")

    table = Table(title="User List", show_header=True, header_style="bold cyan")
    table.add_column("Username")
    table.add_column("Email")
    table.add_column("Description")
    table.add_column("Creation Date")
    table.add_column("Last Connection")
    table.add_column("api_token")
    table.add_column("ssh_key")
    table.add_column("Superadmin")

    for user in users:
        table.add_row(
            user.username,
            user.email,
            user.description,
            user.creation_date.strftime("%Y-%m-%d %H:%M:%S"),
            user.last_connection.strftime("%Y-%m-%d %H:%M:%S"),
            user.api_token,
            user.ssh_key,
            f"[bold][red]{user.superadmin.__str__()}[/bold][/red]",
        )

    console = Console()
    console.print(table)
