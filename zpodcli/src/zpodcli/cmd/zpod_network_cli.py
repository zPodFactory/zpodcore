import time
from typing import Annotated

import typer
from rich import print
from rich.console import Console

from zpodcli.lib.prompt import confirm
from zpodcli.lib.utils import (
    JsonOption,
    NoColorOption,
    console_print,
    exit_with_error,
    json_print,
)
from zpodcli.lib.utils import ZcliTable as Table
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler
from zpodsdk.models.zpod_network_create import ZpodNetworkCreate
from zpodsdk.models.zpod_network_masquerade import ZpodNetworkMasquerade
from zpodsdk.models.zpod_network_routing import ZpodNetworkRouting
from zpodsdk.models.zpod_network_routing_run_view import ZpodNetworkRoutingRunView
from zpodsdk.models.zpod_network_routing_update import ZpodNetworkRoutingUpdate
from zpodsdk.models.zpod_network_routing_view import ZpodNetworkRoutingView
from zpodsdk.models.zpod_network_view import ZpodNetworkView

app = typer.Typer(help="Manage zPod Networks (VLANs on zcore)", no_args_is_help=True)

KINDS = {"zpod", "zcore", "user"}

ZpodNameArg = Annotated[
    str,
    typer.Argument(help="zPod name", show_default=False),
]
NetworkNameArg = Annotated[
    str,
    typer.Argument(help="Network name", show_default=False),
]


def get_masquerade_markdown(value: bool) -> str:
    # True is green like every other boolean; False is muted: not masquerading is
    # the normal state of a network, not a problem.
    if value:
        return "[dark_sea_green4]True[/dark_sea_green4]"
    return "[grey50]False[/grey50]"


def get_kind_markdown(kind: str) -> str:
    match kind:
        case "user":
            return f"[tan]{kind}[/tan]"
        case "zcore":
            # zcore's own VLANs (10/20/30), configured by the image; read-only here
            return f"[grey63]{kind}[/grey63]"
        case _:
            return f"[dark_khaki]{kind}[/dark_khaki]"


def get_routing_markdown(routing: str) -> str:
    match routing:
        case "GLOBAL":
            # Advertised to the whole fabric: the one to notice.
            return f"[dark_orange3 bold]{routing}[/dark_orange3 bold]"
        case "LOCAL":
            return f"[sky_blue2]{routing}[/sky_blue2]"
        case "PENDING":
            return f"[grey63]{routing}...[/grey63]"
        case _:
            return f"[royal_blue1]{routing}[/royal_blue1]"


def get_network_status_markdown(status: str) -> str:
    match status:
        case "ACTIVE":
            return f"[dark_sea_green4]{status}[/dark_sea_green4]"
        case "DISABLED":
            return f"[orange3]{status}[/orange3]"
        case "MISSING":
            return f"[indian_red]{status}[/indian_red]"
        case _:
            return f"[royal_blue1]{status}[/royal_blue1]"


def generate_table(networks: list[ZpodNetworkView], title="zPod Network List"):
    table = Table(
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Name")
    table.add_column("VLAN")
    table.add_column("CIDR")
    table.add_column("Gateway")
    table.add_column("Kind")
    table.add_column("Masquerade")
    table.add_column("Routing")
    table.add_column("Status")

    for network in networks:
        unknown = str(network.status) == "UNKNOWN"
        table.add_row(
            f"[bold]{network.name}[/bold]",
            f"[yellow3]{network.vlan_id}[/yellow3]",
            f"[cornflower_blue]{network.cidr}[/cornflower_blue]",
            f"[sky_blue2]{network.gateway}[/sky_blue2]",
            get_kind_markdown(str(network.kind)),
            "[grey50]?[/grey50]"
            if unknown
            else get_masquerade_markdown(network.masquerade),
            get_routing_markdown(str(network.routing)),
            get_network_status_markdown(str(network.status)),
        )
    console_print(title, table)


def print_network(network: ZpodNetworkView):
    generate_table([network], title="zPod Network")


@app.command(name="list", no_args_is_help=True)
@unexpected_status_handler
def zpod_network_list(
    zpod_name: ZpodNameArg,
    kind: Annotated[
        list[str] | None,
        typer.Option(
            "--kind",
            "-k",
            help=(
                "Only these kinds: zpod (the deploy-time networks), zcore (zcore's own "
                "VLANs 10/20/30), user. Repeat the option or give a comma-separated list."
            ),
            show_default=False,
        ),
    ] = None,
    json_: JsonOption = False,
    no_color: NoColorOption = False,
):
    """
    List networks of a zPod: the zPodFactory networks, zcore's own VLANs and the user VLANs
    """
    kinds = {
        k.strip().lower() for item in (kind or []) for k in item.split(",") if k.strip()
    }
    if unknown := kinds - KINDS:
        exit_with_error(
            f"unknown kind(s): {', '.join(sorted(unknown))}; choose from {', '.join(sorted(KINDS))}"
        )
    z: ZpodClient = ZpodClient()
    networks: list[ZpodNetworkView] = z.zpods_networks_get_all.sync(
        id=f"name={zpod_name}"
    )
    if kinds:
        networks = [n for n in networks if str(n.kind) in kinds]
    if json_:
        json_print([item.to_dict() for item in networks])
    else:
        generate_table(networks)


@app.command(name="add", no_args_is_help=True)
@unexpected_status_handler
def zpod_network_add(
    zpod_name: ZpodNameArg,
    name: Annotated[
        str,
        typer.Option(
            "--name", help="Network name (letters, digits, '-')", show_default=False
        ),
    ],
    vlan: Annotated[
        int,
        typer.Option(
            "--vlan", help="VLAN id (1-4094, not reserved)", show_default=False
        ),
    ],
    gateway: Annotated[
        str,
        typer.Option(
            "--gateway",
            help="Gateway address with prefix, zcore's address on the VLAN (10.42.111.1/24)",
            show_default=False,
        ),
    ],
    masquerade: Annotated[
        bool,
        typer.Option(
            "--masquerade",
            help="Source-translate traffic leaving the zPod on zcore (off by default)",
        ),
    ] = False,
    routing: Annotated[
        str,
        typer.Option(
            "--routing",
            help="local (inside the zPod only) or global (advertised to the fabric, superadmin)",
        ),
    ] = "local",
    no_color: NoColorOption = False,
):
    """
    Add a VLAN network to a zPod
    """
    routing = routing.upper()
    if routing not in ("LOCAL", "GLOBAL"):
        exit_with_error("--routing must be local or global")

    print(
        f"Adding network [magenta]{name}[/magenta] to zPod [magenta]{zpod_name}[/magenta]"
    )
    z: ZpodClient = ZpodClient()
    network = z.zpods_network_add.sync(
        id=f"name={zpod_name}",
        body=ZpodNetworkCreate(
            name=name,
            vlan=vlan,
            gateway=gateway,
            masquerade=masquerade,
            routing=ZpodNetworkRouting(routing),
        ),
    )
    print_network(network)
    if str(network.routing) == "PENDING":
        print(
            "  routing: [grey63]PENDING...[/grey63]  flow run "
            f"[sky_blue2]advertise {zpod_name}/{name}[/sky_blue2] "
            "(checks, evidence and the verdict are in the run)"
        )


@app.command(name="remove", no_args_is_help=True)
@unexpected_status_handler
def zpod_network_remove(
    zpod_name: ZpodNameArg,
    name: NetworkNameArg,
    yes: Annotated[
        bool,
        typer.Option(
            "-y", "--yes", help="Automatic yes to prompts.", show_default=False
        ),
    ] = False,
    no_color: NoColorOption = False,
):
    """
    Remove a VLAN network from a zPod (interface and subnet gone from zcore)
    """
    if not yes:
        confirm(
            f"Are you sure you want to remove network [magenta]{name}[/magenta] "
            f"from zPod [magenta]{zpod_name}[/magenta]?"
        )
    print(
        f"Removing network [magenta]{name}[/magenta] from zPod [magenta]{zpod_name}[/magenta]"
    )
    z: ZpodClient = ZpodClient()
    z.zpods_network_remove.sync(id=f"name={zpod_name}", name=name)
    zpod_network_list(zpod_name)


@app.command(name="masquerade", no_args_is_help=True)
@unexpected_status_handler
def zpod_network_masquerade(
    state: Annotated[
        str,
        typer.Argument(help="on or off", show_default=False),
    ],
    zpod_name: ZpodNameArg,
    name: NetworkNameArg,
    no_color: NoColorOption = False,
):
    """
    Turn source translation (masquerade) on or off for a network
    """
    if state.lower() not in ("on", "off"):
        exit_with_error("state must be on or off")
    enabled = state.lower() == "on"
    verb = "Enabling" if enabled else "Disabling"
    print(
        f"{verb} masquerade on network [magenta]{name}[/magenta] "
        f"of zPod [magenta]{zpod_name}[/magenta]"
    )
    z: ZpodClient = ZpodClient()
    network = z.zpods_network_masquerade.sync(
        id=f"name={zpod_name}",
        name=name,
        body=ZpodNetworkMasquerade(enabled=enabled),
    )
    print_network(network)


@app.command(name="enable", no_args_is_help=True)
@unexpected_status_handler
def zpod_network_enable(
    zpod_name: ZpodNameArg, name: NetworkNameArg, no_color: NoColorOption = False
):
    """
    Bring the VLAN interface up on zcore
    """
    print(
        f"Enabling network [magenta]{name}[/magenta] of zPod [magenta]{zpod_name}[/magenta]"
    )
    z: ZpodClient = ZpodClient()
    print_network(z.zpods_network_enable.sync(id=f"name={zpod_name}", name=name))


@app.command(name="disable", no_args_is_help=True)
@unexpected_status_handler
def zpod_network_disable(
    zpod_name: ZpodNameArg, name: NetworkNameArg, no_color: NoColorOption = False
):
    """
    Bring the VLAN interface down on zcore (not persistent across a zcore reboot)
    """
    print(
        f"Disabling network [magenta]{name}[/magenta] of zPod [magenta]{zpod_name}[/magenta]"
    )
    z: ZpodClient = ZpodClient()
    print_network(z.zpods_network_disable.sync(id=f"name={zpod_name}", name=name))


@app.command(name="routing", no_args_is_help=True)
@unexpected_status_handler
def zpod_network_routing(
    zpod_name: ZpodNameArg,
    name: NetworkNameArg,
    routing: Annotated[
        str,
        typer.Argument(help="local or global", show_default=False),
    ],
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Run the fabric checks only, change nothing"),
    ] = False,
    wait: Annotated[
        bool,
        typer.Option(
            "--wait/--no-wait",
            help="Follow the zpodengine run and print its verdict (default: wait)",
        ),
    ] = True,
    no_color: NoColorOption = False,
):
    """
    Route a network inside the zPod only (local) or advertise it to the NSX
    fabric (global). Superadmin only; runs as an audited zpodengine flow, which
    this command follows until it ends (exit code 1 when it fails).
    """
    routing = routing.upper()
    if routing not in ("LOCAL", "GLOBAL"):
        exit_with_error("routing must be local or global")

    print(
        f"Setting routing [magenta]{routing.lower()}[/magenta] on network "
        f"[magenta]{name}[/magenta] of zPod [magenta]{zpod_name}[/magenta]"
        + (" [grey63](dry run)[/grey63]" if dry_run else "")
    )
    z: ZpodClient = ZpodClient()
    result: ZpodNetworkRoutingView = z.zpods_network_routing.sync(
        id=f"name={zpod_name}",
        name=name,
        body=ZpodNetworkRoutingUpdate(
            routing=ZpodNetworkRouting(routing), dry_run=dry_run
        ),
    )
    network = result.network
    if result.flow_run_id in (None, ""):
        print(
            f"  routing: {get_routing_markdown(str(network.routing))}  (already there, nothing to do)"
        )
        return
    verb = "advertise" if routing == "GLOBAL" else "withdraw"
    print(
        f"  routing: [grey63]PENDING...[/grey63]  flow run "
        f"[sky_blue2]{verb} {zpod_name}/{name}[/sky_blue2] "
        f"[grey50]{result.flow_run_id}[/grey50]"
    )
    if not wait:
        print(
            "  checks, evidence and the verdict are in the run; a failed check puts "
            "the network back to its previous routing"
        )
    if routing == "GLOBAL" and network.masquerade:
        print(
            f"  [yellow3]{name} is masqueraded; masquerading will be turned off once "
            "the route is advertised.[/yellow3]"
        )
    if routing == "LOCAL":
        print(
            f"  [yellow3]once local, {name} has no egress; to restore it: "
            f"zcli zpod network masquerade on {zpod_name} {name}[/yellow3]"
        )
    if not wait:
        return

    run = follow_routing_run(z, zpod_name, name, result.flow_run_id, verb)
    network = run.network
    if run.state == "COMPLETED":
        print(
            f"  routing: {get_routing_markdown(str(network.routing))}  "
            f"masquerade: {get_masquerade_markdown(network.masquerade)}"
            + ("  [grey63](dry run, nothing changed)[/grey63]" if dry_run else "")
        )
        return
    print(
        f"  routing: {get_routing_markdown(str(network.routing))}  "
        f"[indian_red]{run.state}[/indian_red]"
    )
    if run.message:
        print(f"  [indian_red]{run.message}[/indian_red]")
    raise typer.Exit(1)


FINAL_RUN_STATES = ("COMPLETED", "FAILED", "CRASHED", "CANCELLED")


def follow_routing_run(
    z: ZpodClient, zpod_name: str, name: str, flow_run_id: str, verb: str
) -> ZpodNetworkRoutingRunView:
    """Poll the run until it reaches a final state. Ctrl-C leaves it running."""
    console = Console()
    try:
        with console.status(
            f"[grey63]{verb} {zpod_name}/{name}: running in zpodengine...[/grey63]",
            spinner="dots",
        ):
            while True:
                run: ZpodNetworkRoutingRunView = z.zpods_network_routing_run.sync(
                    id=f"name={zpod_name}", name=name, flow_run_id=flow_run_id
                )
                if run.state in FINAL_RUN_STATES:
                    return run
                time.sleep(3)
    except KeyboardInterrupt:
        print(
            f"  still running in zpodengine: run [grey50]{flow_run_id}[/grey50]; "
            f"zcli zpod network list {zpod_name} shows the outcome"
        )
        raise typer.Exit() from None
