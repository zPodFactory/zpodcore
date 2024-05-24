import json
import re
from pathlib import Path
from typing import Optional

import typer
from attrs import fields_dict
from rich import print
from rich.json import JSON
from rich.table import Table
from typing_extensions import Annotated

from zpodcli.cmd import endpoint_permission_cli
from zpodcli.lib.file import load_json_or_yaml_file
from zpodcli.lib.prompt import ask
from zpodcli.lib.utils import console_print, exit_with_error
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler
from zpodsdk.models.endpoint_compute_create import EndpointComputeCreate
from zpodsdk.models.endpoint_compute_drivers import EndpointComputeDrivers
from zpodsdk.models.endpoint_compute_update import EndpointComputeUpdate
from zpodsdk.models.endpoint_compute_view import EndpointComputeView
from zpodsdk.models.endpoint_create import EndpointCreate
from zpodsdk.models.endpoint_network_create import EndpointNetworkCreate
from zpodsdk.models.endpoint_network_drivers import EndpointNetworkDrivers
from zpodsdk.models.endpoint_network_update import EndpointNetworkUpdate
from zpodsdk.models.endpoint_network_view import EndpointNetworkView
from zpodsdk.models.endpoint_update import EndpointUpdate
from zpodsdk.models.endpoints_create import EndpointsCreate
from zpodsdk.models.endpoints_update import EndpointsUpdate
from zpodsdk.types import Unset

app = typer.Typer(help="Manage Endpoints")
app.add_typer(endpoint_permission_cli.app, name="permission")


def endpoint_line(data, key):
    key_color, data_color = "dodger_blue2", "green"
    if isinstance(key, tuple):
        key, key_color, data_color = key

    return (
        f"[{key_color}]{key}[/{key_color}]: "
        f"[{data_color}]{getattr(data, key)}[/{data_color}]"
    )


def endpoint_output(data, keys: list):
    lines = [endpoint_line(data, key) for key in keys]
    return "\n".join(lines)


# Add keys that are not in base to the end
def addl_keys(model, base: dict):
    base_keys = {key[0] if isinstance(key, tuple) else key for key in base}
    model_keys = {x for x in fields_dict(model) if x != "additional_properties"}
    keys_to_add = model_keys - base_keys
    base.extend(sorted(keys_to_add))
    return base


def generate_table(endpoints: list, title: str, all_endpoint_keys=False):
    compute_endpoint_keys = [
        ("driver", "deep_sky_blue1", "spring_green1"),
        "hostname",
        "username",
        "datacenter",
        "resource_pool",
        "storage_datastore",
        "vmfolder",
    ]
    network_endpoint_keys = [
        ("driver", "deep_sky_blue1", "spring_green1"),
        "hostname",
        "username",
        "edgecluster",
        "t0",
        "transportzone",
        "networks",
    ]
    if all_endpoint_keys:
        compute_endpoint_keys = addl_keys(EndpointComputeView, compute_endpoint_keys)
        network_endpoint_keys = addl_keys(EndpointNetworkView, network_endpoint_keys)

    table = Table(
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
        leading=True,
    )
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Compute")
    table.add_column("Network")

    for endpoint in endpoints:
        ep = endpoint.endpoints
        table.add_row(
            f"[dark_khaki]{endpoint.name}[/dark_khaki]",
            endpoint.description,
            endpoint_output(ep.compute, compute_endpoint_keys),
            endpoint_output(ep.network, network_endpoint_keys),
        )
    console_print(title, table)


@app.command(name="list")
@unexpected_status_handler
def endpoint_list():
    """
    List Endpoints
    """
    z = ZpodClient()
    endpoints = z.endpoints_get_all.sync()
    generate_table(endpoints, "Endpoint List")


@app.command(name="info", no_args_is_help=True)
@unexpected_status_handler
def endpoint_info(
    endpoint_name: Annotated[
        str,
        typer.Argument(
            help="Endpoint name",
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
    Endpoint Info
    """
    z = ZpodClient()
    endpoint = z.endpoints_get.sync(id=f"name={endpoint_name}")
    if json_:
        endpoints_dict = endpoint.to_dict()["endpoints"]
        print(JSON.from_data(endpoints_dict, sort_keys=True))
    else:
        generate_table([endpoint], title="Endpoint Info", all_endpoint_keys=True)


@app.command(name="create", no_args_is_help=True)
@unexpected_status_handler
def endpoint_create(
    endpoint_name: Annotated[
        str,
        typer.Argument(
            help="Endpoint name",
            show_default=False,
        ),
    ],
    description: Annotated[
        str,
        typer.Option(
            "--description",
            "-d",
            help="Description",
            show_default=False,
        ),
    ] = "",
    endpoints_str: Annotated[
        str,
        typer.Option(
            "--endpoints",
            "-e",
            help="Endpoints json",
            show_default=False,
        ),
    ] = None,
    endpoints_file: Annotated[
        Optional[Path],
        typer.Option(
            "--endpoints-file",
            "-ef",
            help="File containing endpoints json",
            show_default=False,
        ),
    ] = None,
):
    """
    Endpoint Create
    """
    if endpoints_file and endpoints_str:
        exit_with_error("Can not have both endpoints file and endpoints")

    if endpoints_str or endpoints_file:
        if endpoints_file:
            endpoints_dict = load_json_or_yaml_file(endpoints_file)
        else:
            try:
                endpoints_dict = json.loads(endpoints_str)
            except json.JSONDecodeError:
                exit_with_error("The provided JSON was invalid")

        if "compute" not in endpoints_dict:
            exit_with_error("The compute section was not found in the json")

        if "network" not in endpoints_dict:
            exit_with_error("The network section was not found in the json")

        errors = []
        endpoint_compute_dict = endpoints_dict["compute"]
        if err_c := validate_keywords(
            "compute",
            actual_keys=set(endpoint_compute_dict.keys()),
            expected_keys=set(fields_dict(EndpointComputeCreate)),
        ):
            errors.append(err_c)

        endpoint_network_dict = endpoints_dict["network"]
        if err_n := validate_keywords(
            "network",
            actual_keys=set(endpoint_network_dict.keys()),
            expected_keys=set(fields_dict(EndpointNetworkCreate)),
        ):
            errors.append(err_n)

        if errors:
            exit_with_error("\n  ".join(errors))
    else:
        print("\nCompute Endpoint")
        endpoint_compute_dict = {
            "driver": ask(
                "driver",
                choices=list(EndpointComputeDrivers),
                default=EndpointComputeDrivers.VSPHERE,
            ),
            "hostname": ask("hostname", validation=validate_hostname),
            "username": ask("username"),
            "password": ask("password", password=True),
            "datacenter": ask("datacenter"),
            "resource_pool": ask("resource_pool"),
            "storage_policy": "",
            "storage_datastore": ask("storage_datastore"),
            "contentlibrary": "",
            "vmfolder": ask("vmfolder"),
        }

        print("\nNetwork Endpoint")
        endpoint_network_dict = {
            "driver": ask(
                "driver",
                choices=list(EndpointNetworkDrivers),
                default=EndpointNetworkDrivers.NSXT_PROJECTS,
            ),
            "hostname": ask("hostname", validation=validate_hostname),
            "username": ask("username", default="admin"),
            "password": ask("password", password=True),
            "networks": ask("networks"),
            "transportzone": ask("transportzone"),
            "edgecluster": ask("edgecluster"),
            "t0": ask("t0"),
        }

    endpoint_compute_model = EndpointComputeCreate(**endpoint_compute_dict)
    endpoint_compute_dict["driver"] = endpoint_compute_dict["driver"].lower()
    endpoint_network_dict["driver"] = EndpointNetworkDrivers(
        endpoint_network_dict["driver"].lower()
    )
    endpoint_network_model = EndpointNetworkCreate(**endpoint_network_dict)

    z: ZpodClient = ZpodClient()
    z.endpoints_create.sync(
        body=EndpointCreate(
            name=endpoint_name,
            endpoints=EndpointsCreate(
                compute=endpoint_compute_model,
                network=endpoint_network_model,
            ),
            description=description,
        )
    )
    print(f"Endpoint [magenta]{endpoint_name}[/magenta] has been created.")


@app.command(name="update", no_args_is_help=True)
@unexpected_status_handler
def endpoint_update(
    endpoint_name: Annotated[
        str,
        typer.Argument(
            help="Endpoint name",
            show_default=False,
        ),
    ],
    newname: Annotated[
        Optional[str],
        typer.Option(
            "--newname",
            help="New endpoint name",
            show_default=False,
        ),
    ] = None,
    description: Annotated[
        str,
        typer.Option(
            "--description",
            "-d",
            help="Description",
            show_default=False,
        ),
    ] = "",
    compute_username: Annotated[
        str,
        typer.Option(
            "--compute-username",
            "-cu",
            help="Compute Username",
            show_default=False,
        ),
    ] = None,
    compute_password: Annotated[
        str,
        typer.Option(
            "--compute-password",
            "-cp",
            help="Compute Password",
            show_default=False,
        ),
    ] = None,
    network_username: Annotated[
        str,
        typer.Option(
            "--network-username",
            "-nu",
            help="Network Username",
            show_default=False,
        ),
    ] = None,
    network_password: Annotated[
        str,
        typer.Option(
            "--network-password",
            "-np",
            help="Network Password",
            show_default=False,
        ),
    ] = None,
):
    """
    Endpoint Update
    """
    z: ZpodClient = ZpodClient()
    endpoint = EndpointUpdate()
    if newname and newname != endpoint_name:
        endpoint.name = newname

    if description:
        endpoint.description = description

    if compute_username or compute_password:
        endpoint.endpoints = EndpointsUpdate()
        endpoint.endpoints.compute = EndpointComputeUpdate(
            username=compute_username or Unset(),
            password=compute_password or Unset(),
        )

    if network_username or network_password:
        if not endpoint.endpoints:
            endpoint.endpoints = EndpointsUpdate()

        endpoint.endpoints.network = EndpointNetworkUpdate(
            username=network_username or Unset(),
            password=network_password or Unset(),
        )

    if not endpoint.name and not endpoint.description and not endpoint.endpoints:
        exit_with_error("No changes specified")

    z.endpoints_update.sync(
        id=f"name={endpoint_name}",
        body=endpoint,
    )
    print(f"Endpoint [magenta]{endpoint_name}[/magenta] has been updated.")


@app.command(name="delete", no_args_is_help=True)
@unexpected_status_handler
def endpoint_delete(
    endpoint_name: Annotated[
        str,
        typer.Argument(
            help="Endpoint name",
            show_default=False,
        ),
    ],
):
    """
    Endpoint Delete
    """
    z: ZpodClient = ZpodClient()
    z.endpoints_delete.sync(id=f"name={endpoint_name}")
    print(f"Endpoint [magenta]{endpoint_name}[/magenta] has been deleted successfully")


def validate_keywords(section, expected_keys: set, actual_keys: set) -> str | None:
    errors = []
    missing_keys = expected_keys - actual_keys
    if len(missing_keys):
        errors.append(f"the following item(s) are missing: {', '.join(missing_keys)}")

    extra_keys = actual_keys - expected_keys
    if len(extra_keys):
        errors.append(f"the following item(s) are extra: {', '.join(extra_keys)}")

    if errors:
        return f"In the {section} section, {' and '.join(errors)}"


def validate_hostname(hostname: str) -> bool:
    """
    https://en.m.wikipedia.org/wiki/Fully_qualified_domain_name
    """
    if not 1 < len(hostname) < 253:
        return False

    # Remove trailing dot
    if hostname[-1] == ".":
        hostname = hostname[:-1]

    #  Split hostname into list of DNS labels
    labels = hostname.split(".")

    #  Define pattern of DNS label
    #  Can begin and end with a number or letter only
    #  Can contain hyphens, a-z, A-Z, 0-9
    #  1 - 63 chars allowed
    fqdn = re.compile(r"^[a-z0-9]([a-z-0-9-]{0,61}[a-z0-9])?$", re.IGNORECASE)

    # Check that all labels match that pattern.
    return all(fqdn.match(label) for label in labels)
