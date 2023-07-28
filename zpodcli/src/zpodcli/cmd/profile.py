import json
from pathlib import Path

import typer
import yaml
from rich import print
from rich.table import Table
from zpod.models.profile_create import ProfileCreate
from zpod.models.profile_item_create import ProfileItemCreate
from zpod.models.profile_item_update import ProfileItemUpdate
from zpod.models.profile_update import ProfileUpdate

from zpodcli.lib import utils, zpod_client

app = typer.Typer(help="Manage profiles")


def generate_table(profiles: list, action: str = None):
    table = Table(
        "Profile",
        "Components",
        title=f"{action} Profile ",
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    for profile in profiles:
        profile_item_lines = []
        for profile_item in walk_profile(profile.profile):
            data_values = []
            if _ := profile_item.last_octet:
                data_values.append(f"Last Octet: {_}")
            if _ := profile_item.vcpu:
                data_values.append(f"CPU: {_}")
            if _ := profile_item.vmem:
                data_values.append(f"Mem: {_}GB")

            profile_item_txt = f"[yellow3]{profile_item.component_uid}[/yellow3]"
            if data_values:
                profile_item_txt += (
                    f"[light_cyan3] ({', '.join(data_values)})[/light_cyan3]"
                )
            profile_item_lines.append(profile_item_txt)

        table.add_row(
            f"[tan]{profile.name}[/tan]",
            "\n".join(profile_item_lines),
        )
    print(table)


@app.command(name="list")
def profile_list():
    """
    List profiles
    """
    z = zpod_client.ZpodClient()
    result = z.profiles_get_all.sync_detailed()

    if result.status_code == 200:
        generate_table(result.parsed, "List")
    else:
        utils.handle_response(result)


@app.command(name="create", no_args_is_help=True)
def profile_create(
    name: str = typer.Option(..., "--name", "-n"),
    profile_file: Path = typer.Option(..., "--profile_file", "-pf"),
):
    """
    Create Profile
    """
    profile_obj = load_profile_file(profile_file)

    z = zpod_client.ZpodClient()
    result = z.profiles_create.sync_detailed(
        json_body=ProfileCreate(
            name=name,
            profile=build_profile(profile_obj),
        )
    )

    if result.status_code == 201:
        print(f"Profile [magenta]{name}[/magenta] has been created.")
    else:
        utils.handle_response(result)


@app.command(name="update", no_args_is_help=True)
def profile_update(
    name: str = typer.Option(..., "--name", "-n"),
    newname: str = typer.Option(None, "--newname"),
    profile_file: Path = typer.Option(None, "--profile_file", "-pf"),
):
    """
    Update Profile
    """
    profile_update = ProfileUpdate()
    if newname and newname != name:
        profile_update.name = newname

    if profile_file:
        profile_obj = load_profile_file(profile_file)
        profile_update.profile = build_profile(profile_obj, False)

    z = zpod_client.ZpodClient()
    result = z.profiles_update.sync_detailed(
        id=f"name={name}",
        json_body=profile_update,
    )
    if result.status_code == 201:
        print(f"Profile [magenta]{name}[/magenta] has been updated.")
    else:
        utils.handle_response(result)


def load_profile_file(profile_file):
    extension = profile_file.suffix
    with profile_file.open() as f:
        if extension in (".yaml", ".yml"):
            return yaml.safe_load(f)
        elif extension == ".json":
            return json.load(f)


def build_profile(profile_obj, is_create=True):
    profile_objects = []
    for profile_item in profile_obj:
        if isinstance(profile_item, list):
            item = [
                parse_profile_item(sub_profile_item)
                for sub_profile_item in profile_item
            ]
        else:
            item = parse_profile_item(profile_item, is_create)
        profile_objects.append(item)
    return profile_objects


def parse_profile_item(profile_item, is_create=True):
    """Normal to_dict doesn't report if there are extra fields included.  This will."""
    if is_create:
        profile_item = ProfileItemCreate(**profile_item)
    else:
        profile_item = ProfileItemUpdate(**profile_item)
    return profile_item


def walk_profile(profile_obj):
    for profile_item in profile_obj:
        if isinstance(profile_item, list):
            yield from profile_item
        else:
            yield profile_item
