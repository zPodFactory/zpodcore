"""Where a component is deployed: L1 on the endpoint, or L2 nested in the zPod.

The library JSON's ``component_isnested`` is the default; a component add or a
profile item can override it with ``nested``.
"""

import json

from zpodcommon.lib.component_network import clean_network

# Protected components: they have their own deploy path in zpod_component_add_3_deploy,
# which fixes their placement, so ``nested`` accepts only their own default and
# ``network`` is refused. Keep both in sync:
# zpodengine/tests/test_component_placement_guard.py fails when they differ.
PROTECTED_COMPONENTS = frozenset(
    {
        "zcore",
        "vyos",
        "vcsa",
        "esxi",
        "proxmox",
        "proxmox-dm",
        "proxmox-bs",
        "cloudbuilder",
        "vcfinstaller",
    }
)


def nested_override_error(
    component_name: str, nested: bool | None, component_json: dict | None = None
) -> str | None:
    """Why ``nested`` can't be set on this component, or None when it can.

    A protected component accepts its own default (vcsa nested, esxi on the
    endpoint): only a change of placement is refused.
    """
    if nested is None or component_name not in PROTECTED_COMPONENTS:
        return None
    default = component_isnested(component_json, None)
    if nested == default:
        return None
    where = "nested in the zPod" if default else "on the endpoint"
    return (
        f"nested can't be set to {str(nested).lower()} on {component_name}: "
        f"its placement is fixed ({where})"
    )


def component_isnested(component_json: dict | None, nested: bool | None) -> bool:
    """The override when set, else the library JSON's component_isnested."""
    if nested is not None:
        return nested
    return bool((component_json or {}).get("component_isnested", False))


def component_options_error(
    component_name: str,
    component_json: dict | None,
    *,
    nested: bool | None = None,
    network: dict | None = None,
    vnics: int | None = None,
    vlan_id: int | None = None,
) -> str | None:
    """Why these deploy options can't go together on this component, or None.

    `network` and the one-portgroup rule are for nested components only: every
    NIC of a nested component goes on its portgroup, so `vnics` is refused there.
    """
    network = clean_network(network)
    if error := nested_override_error(component_name, nested, component_json):
        return error
    if vlan_id is not None:
        # vlan_id gives the address: ip would give another one. portgroup,
        # gateway and dns combine with it (a nested trunk portgroup).
        if network and network.get("ip"):
            return "vlan_id gives the address: set it, or network.ip"
        if not 1 <= vlan_id <= 4094:
            return f"vlan_id {vlan_id} is not a VLAN (1-4094)"
        # Only a guest that is told its VLAN can tag its interface (ESXi).
        if "zpod_vlan" not in json.dumps(component_json or {}):
            return (
                f"vlan_id can't be set on {component_name}: its library JSON "
                "doesn't use {{zpod_vlan}}"
            )
    if component_name in PROTECTED_COMPONENTS:
        if network:
            return f"network can't be set on {component_name}: component is protected"
        return None
    isnested = component_isnested(component_json, nested)
    if network and not isnested:
        return (
            f"network is only for nested components: {component_name} deploys on "
            "the endpoint (set nested to true)"
        )
    if vnics is not None and isnested:
        return (
            f"vnics can't be set on a nested component: {component_name} keeps the "
            "NICs of its OVA, all on one portgroup"
        )
    spec = (component_json or {}).get("component_deploy_govc_spec") or {}
    if network and network.get("portgroup") and not spec.get("NetworkMapping"):
        return (
            f"portgroup can't be set on {component_name}: its library JSON has no "
            "NetworkMapping"
        )
    return None
