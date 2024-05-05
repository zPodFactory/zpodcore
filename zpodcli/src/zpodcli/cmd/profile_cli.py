import json
from pathlib import Path
from typing import Optional

import typer
from rich import print
from rich.json import JSON
from rich.table import Table
from typing_extensions import Annotated

from zpodcli.lib.file import load_json_or_yaml_file
from zpodcli.lib.utils import console_print, exit_with_error
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler
from zpodsdk.models.profile_create import ProfileCreate
from zpodsdk.models.profile_item_create import ProfileItemCreate
from zpodsdk.models.profile_item_update import ProfileItemUpdate
from zpodsdk.models.profile_update import ProfileUpdate

app = typer.Typer(help="Manage Profiles")


def generate_table(profiles: list, action: str = None):
    title = f"Profile {action}"
    table = Table(
        "Name",
        "Components",
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    for profile in sorted(profiles, key=lambda p: p.name):
        table.add_row(
            f"[tan]{profile.name}[/tan]",
            profile_item_output(profile),
        )
    console_print(title, table)


def profile_item_output(profile):
    profile_item_lines = []
    for profile_item in walk_profile(profile.profile):
        data_values = []
        if host_id := profile_item.host_id:
            data_values.append(f"Host Id: {host_id}")
        if vcpu := profile_item.vcpu:
            data_values.append(f"CPU: {vcpu}")
        if vmem := profile_item.vmem:
            data_values.append(f"Mem: {vmem}GB")
        if vdisks := profile_item.vdisks:
            vdisks_txt = ", ".join([f"{vdisk}GB" for vdisk in vdisks])
            data_values.append(f"Disks: {vdisks_txt}")
        profile_item_txt = f"[yellow3]{profile_item.component_uid}[/yellow3]"
        if data_values:
            profile_item_txt += (
                f"[light_cyan3] ({', '.join(data_values)})[/light_cyan3]"
            )
        profile_item_lines.append(profile_item_txt)
    return "\n".join(profile_item_lines)


@app.command(name="list")
@unexpected_status_handler
def profile_list():
    """
    Profile List
    """
    z: ZpodClient = ZpodClient()
    profiles = z.profiles_get_all.sync()
    generate_table(profiles, "List")


@app.command(name="info", no_args_is_help=True)
@unexpected_status_handler
def profile_info(
    profile_name: Annotated[
        str,
        typer.Argument(
            help="Profile name",
            show_default=False,
        ),
    ],
    json_: Annotated[
        bool,
        typer.Option(
            "--json",
            "-j",
            help="Display using json",
            is_flag=True,
        ),
    ] = False,
):
    """
    Profile Info
    """
    z: ZpodClient = ZpodClient()
    profile = z.profiles_get.sync(id=f"name={profile_name}")
    if json_:
        profile_dict = profile.to_dict()["profile"]
        print(JSON.from_data(profile_dict, sort_keys=True))
    else:
        generate_table([profile], "Info")


@app.command(name="create", no_args_is_help=True)
@unexpected_status_handler
def profile_create(
    profile_name: Annotated[
        str,
        typer.Argument(
            help="Profile name",
            show_default=False,
        ),
    ],
    profile_str: Annotated[
        Optional[str],
        typer.Option(
            "--profile",
            "-p",
            help="Profile json",
            show_default=False,
        ),
    ] = None,
    profile_file: Annotated[
        Optional[Path],
        typer.Option(
            "--profile-file",
            "-pf",
            help="File containing profile json",
            show_default=False,
        ),
    ] = None,
):
    """
    Profile Create
    """
    if not profile_file and not profile_str:
        exit_with_error("Must have either profile file or profile")
    if profile_file and profile_str:
        exit_with_error("Can not have both profile file and profile")

    if profile_file:
        profile_obj = load_json_or_yaml_file(profile_file)
    else:
        try:
            profile_obj = json.loads(profile_str)
        except json.JSONDecodeError:
            exit_with_error("Invalid JSON")

    z: ZpodClient = ZpodClient()
    z.profiles_create.sync(
        body=ProfileCreate(
            name=profile_name,
            profile=build_profile(profile_obj),
        )
    )

    print(f"Profile [magenta]{profile_name}[/magenta] has been created.")


@app.command(name="update", no_args_is_help=True)
@unexpected_status_handler
def profile_update(
    profile_name: Annotated[
        str,
        typer.Argument(
            help="Profile name",
            show_default=False,
        ),
    ],
    newname: Annotated[
        Optional[str],
        typer.Option(
            "--newname",
            help="New profile name",
            show_default=False,
        ),
    ] = None,
    profile: Annotated[
        Optional[str],
        typer.Option(
            "--profile",
            "-p",
            help="Profile json",
            show_default=False,
        ),
    ] = None,
    profile_file: Annotated[
        Optional[Path],
        typer.Option(
            "--profile-file",
            "-pf",
            help="File containing profile json",
            show_default=False,
        ),
    ] = None,
):
    """
    Profile Update
    """
    if profile_file and profile:
        exit_with_error("Can not have both profile file and profile")

    z: ZpodClient = ZpodClient()
    if not profile_file and not profile and not newname:
        exit_with_error("No changes provided")

    profile_update = ProfileUpdate()
    if newname and newname != profile_name:
        profile_update.name = newname

    if profile_file:
        profile_obj = load_json_or_yaml_file(profile_file)
        profile_update.profile = build_profile(profile_obj, False)
    elif profile:
        profile_obj = json.loads(profile)
        profile_update.profile = build_profile(profile_obj, False)

    z.profiles_update.sync(
        id=f"name={profile_name}",
        body=profile_update,
    )
    print(f"Profile [magenta]{profile_name}[/magenta] has been updated.")


@app.command(name="delete", no_args_is_help=True)
@unexpected_status_handler
def profile_delete(
    profile_name: Annotated[
        str,
        typer.Argument(
            help="Profile name",
            show_default=False,
        ),
    ],
):
    """
    Profile Delete
    """
    z: ZpodClient = ZpodClient()
    z.profiles_delete.sync(id=f"name={profile_name}")
    print(f"Profile [magenta]{profile_name}[/magenta] has been deleted successfully")


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
