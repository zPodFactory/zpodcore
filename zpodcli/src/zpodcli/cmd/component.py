import typer
from rich.console import Console
from rich.table import Table

from zpodcli.lib import zpod_client

app = typer.Typer(help="Manage components")

console = Console()


def generate_table(components: list, component_uid: str = None, action: str = None):
    title = f"{action} {component_uid}" if len(components) == 1 else "Component List"

    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("UID")
    table.add_column("Name", style="dim")
    table.add_column("Version")
    table.add_column("Library", style="dim")
    table.add_column("Description")
    table.add_column("Enabled", style="dim")
    table.add_column("Status")
    for component in components:
        table.add_row(
            f"[green]{component.component_uid}[/green]",
            f"[magenta]{component.component_name}[/magenta]",
            component.component_version,
            f"[yellow]{component.library_name}[/yellow]",
            f"[green]{component.component_description}[/green]",
            f"[magenta]{component.enabled.__str__()}[/magenta]",
            component.status,
        )
    console.print(table)


@app.command()
def list():
    z = zpod_client.ZpodClient()
    components = z.components_get_all.sync()
    generate_table(components)


@app.command()
def enable(component_uid: str = typer.Option(..., "--uid")):
    z = zpod_client.ZpodClient()
    component = z.components_enable.sync(id=f"uid={component_uid}")
    generate_table(components=[component], component_uid=component_uid, action="Enable")


@app.command()
def get(component_uid: str = typer.Option(..., "--uid")):
    z = zpod_client.ZpodClient()
    component = z.components_get.sync(id=f"uid={component_uid}")

    generate_table(components=[component], component_uid=component_uid, action="Get")


@app.command()
def disable(component_uid: str = typer.Option(..., "--uid")):
    z = zpod_client.ZpodClient()
    component = z.components_disable.sync(id=f"uid={component_uid}")
    generate_table(
        components=[component], component_uid=component_uid, action="Disable"
    )
