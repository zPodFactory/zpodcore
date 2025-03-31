from datetime import datetime
from ipaddress import IPv4Network
from typing import Annotated

import typer
from rich import print
from rich.console import Group
from rich.json import JSON
from rich.panel import Panel
from rich.table import Table, box

from zpodcli.lib.utils import console_print, get_status_markdown
from zpodcli.lib.zpod_client import ZpodClient, unexpected_status_handler
from zpodsdk.models.zpod_permission import ZpodPermission
from zpodsdk.models.zpod_view import ZpodView

app = typer.Typer(help="Manage zPod Info", no_args_is_help=True)


def generate_detailed_info(zpod: ZpodView, fields: str = "bnc"):
    """Generate detailed information about a zPod

    Args:
        zpod: The zPod to display information for
        fields: String containing which panels to display:
               b - Basic Information
               n - Networks
               c - Components
    """
    # Find zbox component and get its IP once for all networks
    zbox_component = next(
        (comp for comp in zpod.components if comp.component.component_name == "zbox"),
        None,
    )
    zbox_ip = zbox_component.ip if zbox_component else "Not found"

    # Get full endpoint information
    z: ZpodClient = ZpodClient()
    endpoint = z.endpoints_get.sync(id=f"name={zpod.endpoint.name}")

    # Format dates in human readable form
    created_at = zpod.creation_date.strftime("%Y-%m-%d %H:%M:%S")
    updated_at = zpod.last_modified_date.strftime("%Y-%m-%d %H:%M:%S")

    # Calculate relative times
    now = datetime.now()
    created_days = (now - zpod.creation_date).days
    updated_days = (now - zpod.last_modified_date).days
    created_relative = f"({created_days} days ago)" if created_days > 0 else "(today)"
    updated_relative = f"({updated_days} days ago)" if updated_days > 0 else "(today)"

    # Get owner information
    owners = []
    for perm in zpod.permissions:
        if perm.permission == ZpodPermission.OWNER:
            owners.extend(user.username for user in perm.users)
    owner_display = ", ".join(sorted(owners))

    # Basic Information Panel
    if "b" in fields:
        basic_info_panel = Panel(
            f"""
[bold]Name:[/bold] {zpod.name}
[bold]Domain:[/bold] [sky_blue2]{zpod.domain}[/sky_blue2]
[bold]Profile:[/bold] [tan]{zpod.profile}[/tan]
[bold]Endpoint:[/bold] [dark_khaki]{endpoint.name}[/dark_khaki] ([yellow]{endpoint.endpoints.compute.driver}[/yellow]: [sky_blue2]{endpoint.endpoints.compute.hostname}[/sky_blue2], [yellow]{endpoint.endpoints.network.driver}[/yellow]: [sky_blue2]{endpoint.endpoints.network.hostname}[/sky_blue2])
[bold]Description:[/bold] {zpod.description or "N/A"}
[bold]Owner:[/bold] [light_pink1]{owner_display}[/light_pink1]
[bold]Password:[/bold] [bold red]{zpod.password}[/bold red]
[bold]Features:[/bold] {",".join(zpod.features.to_dict().keys()) or "None"}
[bold]Created:[/bold] {created_at} [orange3]{created_relative}[/orange3]
[bold]Last Modified:[/bold] {updated_at} [orange3]{updated_relative}[/orange3]
[bold]Status:[/bold] {get_status_markdown(zpod.status)}
""",
            title="Basic Information",
            border_style="blue",
            padding=(1, 2),
        )
        console_print("Basic Information", basic_info_panel)

    # Networks Panel
    if "n" in fields:
        if not zpod.networks:
            networks_panel = Panel(
                "No networks configured for this zPod yet.",
                title="Networks",
                border_style="yellow",
                padding=(1, 2),
            )
            console_print("Networks", networks_panel)
            return

        networks_table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
            padding=(0, 2),
            show_lines=True,
            border_style="dim white",
        )
        networks_table.add_column("Network CIDR")
        networks_table.add_column("Netmask")
        networks_table.add_column("Gateway")
        networks_table.add_column("DNS")
        networks_table.add_column("VLAN ID")
        networks_table.add_column("Router")

        for network in zpod.networks:
            ipv4network = IPv4Network(network.cidr)
            gateway = str(ipv4network.network_address + 1)
            # Extract VLAN from CIDR's last digit
            network_part = str(ipv4network.network_address)
            vlan_id = int(network_part.split(".")[-1])
            vlan_display = "None (Untagged)" if vlan_id == 0 else str(vlan_id)
            router = (
                "zPodFactory Endpoint NSX-T1" if vlan_id == 0 else f"zbox.{zpod.domain}"
            )
            # Calculate netmask from prefix length
            netmask = str(ipv4network.netmask)
            networks_table.add_row(
                f"[bold]{network.cidr}[/bold]",
                f"[cornflower_blue]{netmask}[/cornflower_blue]",
                gateway,
                f"{zbox_ip} [sky_blue2](zbox)[/sky_blue2]",
                f"[cornflower_blue]{vlan_display}[/cornflower_blue]",
                f"[dark_khaki]{router}[/dark_khaki]",
            )

        # Get the first network for NSX-T1 and zbox eth0
        nsx_network = zpod.networks[0]
        nsx_ipv4network = IPv4Network(nsx_network.cidr)
        nsx_gateway = str(nsx_ipv4network.network_address + 1)

        # Get zbox IP
        zbox_component = next(
            (
                comp
                for comp in zpod.components
                if comp.component.component_name == "zbox"
            ),
            None,
        )
        zbox_ip = zbox_component.ip if zbox_component else "N/A"

        # Create static routes text
        static_routes = []
        for network in zpod.networks:
            if int(network.cidr.split("/")[0].split(".")[-1]) != 0:  # Skip native VLAN
                static_routes.append(
                    f"        ║      - [sky_blue2]{network.cidr}[/sky_blue2] to [yellow3]{zbox_ip}[/yellow3] ([yellow3]zbox[/yellow3])"
                )

        # Calculate T0 box width based on T0 value and header text
        t0_header = "NSX T0"
        t0_content = endpoint.endpoints.network.t0
        t0_width = max(
            len(t0_content) + 8,  # T0 value + padding
            len(t0_header) + 8,  # Header text + padding
            15,  # Minimum width
        )
        t0_box = f"""
 ┌{"─" * t0_width}┐
 │ {" " * (t0_width - 2)} │ zPodFactory Endpoint: [sky_blue2]{endpoint.endpoints.network.hostname}[/sky_blue2] ([yellow]{endpoint.endpoints.network.driver}[/yellow])
 │ {t0_header:^{t0_width - 2}} │ zPodFactory Networks: [sky_blue2]{endpoint.endpoints.network.networks}[/sky_blue2]
 │ [dark_sea_green4]{t0_content:^{t0_width - 2}}[/dark_sea_green4] │
 │ {" " * (t0_width - 2)} │ Edge Cluster: [light_pink1]{endpoint.endpoints.network.edgecluster}[/light_pink1]
 └{"─" * t0_width}┘
        │
        │ NSX T0/T1 Auto-plumbing ([tan]100.64.0.0/10[/tan] CGNAT)
        │"""

        # Calculate T1 box width based on content
        t1_header = "NSX T1"
        t1_content = f"zPod-{zpod.name}-tier1"
        t1_width = max(
            len(t1_header) + 8,  # Header + padding
            len(t1_content) + 8,  # Content + padding
            15,  # Minimum width
        )
        t1_box = f""" ┌{"─" * t1_width}┐
 │ {t1_header:^{t1_width - 2}} │
 │ [dark_sea_green4]{t1_content:^{t1_width - 2}}[/dark_sea_green4] │ Edge Cluster: [light_pink1]{endpoint.endpoints.network.edgecluster}[/light_pink1]
 └{"─" * t1_width}┘
        ║`- [sky_blue2]{nsx_gateway}/{nsx_ipv4network.prefixlen}[/sky_blue2] (zPod Management Network)
        ║
        ║     NSX-T1 Static routes to [yellow3]zbox[/yellow3] connected interface ([yellow3]eth0[/yellow3])
{chr(10).join(static_routes)}
        ║
        ║ [dark_sea_green4]zPod-{zpod.name}-segment[/dark_sea_green4] ([cyan]{endpoint.endpoints.network.transportzone}[/cyan])
        ║ - This NSX Segment carries VLANs [magenta]\\[0-4094][/magenta] (802.1Q Trunk)
        ║ """

        # Calculate zbox box width based on content
        zbox_header = "zbox"
        # Calculate width based only on interface names
        interface_names = ["eth0", "eth1.64", "eth1.128", "eth1.192"]
        max_interface_width = (
            max(len(name) for name in interface_names) + 8
        )  # Add padding
        zbox_width = max(
            len(zbox_header) + 8,  # Header + padding
            max_interface_width,  # Interface names + padding
            15,  # Minimum width
        )

        # First calculate the maximum length of all IP/CIDR strings
        ip_lengths = []
        for network in zpod.networks:
            ipv4network = IPv4Network(network.cidr)
            if int(network.cidr.split("/")[0].split(".")[-1]) == 0:
                # For eth0
                ip_lengths.append(len(f"{zbox_ip}/{ipv4network.prefixlen}"))
            else:
                # For eth1.X
                gateway = str(ipv4network.network_address + 1)
                ip_lengths.append(len(f"{gateway}/{ipv4network.prefixlen}"))
        max_ip_length = max(ip_lengths)

        # Create the interface information outside the box
        interface_info = []
        for network in zpod.networks:
            ipv4network = IPv4Network(network.cidr)
            gateway = str(ipv4network.network_address + 1)
            vlan_id = int(network.cidr.split("/")[0].split(".")[-1])
            if vlan_id == 0:
                ip_str = f"{zbox_ip}/{ipv4network.prefixlen}"
                interface_info.append(
                    f" │ [yellow3]eth0[/yellow3]           │ - [yellow3]{ip_str}{' ' * (max_ip_length - len(ip_str))}[/yellow3] [cornflower_blue](None - Untagged)[/cornflower_blue]"
                )
            else:
                ip_str = f"{gateway}/{ipv4network.prefixlen}"
                interface_info.append(
                    f" │ eth1.[cornflower_blue]{vlan_id:<6}[/cornflower_blue]    │ - [sky_blue2]{ip_str}{' ' * (max_ip_length - len(ip_str))}[/sky_blue2] [cornflower_blue](VLAN {vlan_id})[/cornflower_blue]"
                )

        # Create the zbox box with just the interface names
        zbox_box = f""" ┌{"─" * zbox_width}┐
 │ {zbox_header:^{zbox_width - 2}} │
 │ {" " * (zbox_width - 2)} │
{chr(10).join(interface_info)}
 └{"─" * zbox_width}┘"""

        networks_panel = Panel(
            Group(
                "Networks available for this zPod and advertised in the whole zPodFactory environment:\n",
                networks_table,
                "\nzPod Network Diagram:",
                t0_box,
                t1_box,
                zbox_box,
            ),
            title="Networks",
            border_style="yellow",
            padding=(1, 2),
        )
        console_print("Networks", networks_panel)

    # Components Panel
    if "c" in fields:
        components_table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
            padding=(0, 2),
            show_lines=True,
            border_style="dim white",
        )
        components_table.add_column("Component")
        components_table.add_column("Component UID")
        components_table.add_column("IP")
        components_table.add_column("Access URL")
        components_table.add_column(
            "Credentials ([dark_khaki]UI[/dark_khaki]/[light_pink1]SSH[/light_pink1])"
        )
        components_table.add_column("Status")

        # Sort components by IP address
        sorted_components = sorted(
            zpod.components,
            key=lambda x: [int(i) for i in x.ip.split(".")] if x.ip else [0, 0, 0, 0],
        )

        # Add components in IP order
        for component in sorted_components:
            # Format credentials and access URLs if available
            cred_lines = []
            access_urls = []
            if component.usernames:
                for username in component.usernames:
                    if username.additional_properties["type"] == "ui":
                        cred_lines.append(
                            f"[dark_khaki]UI:[/dark_khaki] {username.additional_properties['username']}"
                        )
                        access_urls.append(
                            f"[dark_khaki]UI:[/dark_khaki] [sky_blue2]https://{component.fqdn}[/sky_blue2]"
                        )
                    elif username.additional_properties["type"] == "ssh":
                        cred_lines.append(
                            f"[light_pink1]SSH:[/light_pink1] {username.additional_properties['username']}"
                        )
                        access_urls.append(
                            f"[light_pink1]SSH:[/light_pink1] [sky_blue2]ssh://{component.fqdn}[/sky_blue2]"
                        )

            # Join multiple lines with newlines if they exist, otherwise show N/A
            credentials = "\n".join(cred_lines) if cred_lines else "N/A"
            access_url = "\n".join(access_urls) if access_urls else "N/A"

            components_table.add_row(
                component.hostname,
                f"[yellow3]{component.component.component_uid}[/yellow3]",
                component.ip or "N/A",
                access_url,
                credentials,
                get_status_markdown(component.status),
            )

        # Create the components panel content
        panel_content = []
        panel_content.append("Components deployed in the zPod:\n")
        panel_content.append(components_table)
        if zpod.password:
            panel_content.append(
                Panel(
                    f"[bold]Components Password:[/bold] [bold red]{zpod.password}[/bold red]",
                    border_style="red",
                    padding=(0, 1),
                    expand=False,
                )
            )

        components_panel = Panel(
            Group(*panel_content),
            title="Components",
            border_style="green",
            padding=(1, 2),
        )
        console_print("Components", components_panel)


@app.command(name="info", no_args_is_help=True)
@unexpected_status_handler
def zpod_info(
    zpod_name: Annotated[
        str,
        typer.Argument(
            help="zPod name",
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
    fields: Annotated[
        str,
        typer.Option(
            "--fields",
            "-f",
            help="Display specific information panels (b:Basic, n:Networking, c:Components)",
            show_default=False,
        ),
    ] = "bnc",
):
    """
    Display zPod Detailed information
    """
    z: ZpodClient = ZpodClient()
    zpod = z.zpods_get.sync(id=f"name={zpod_name}")

    if json_:
        zpod_dict = zpod.to_dict()
        print(JSON.from_data(zpod_dict, sort_keys=True))
    else:
        generate_detailed_info(zpod, fields)
