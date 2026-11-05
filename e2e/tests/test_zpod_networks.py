"""zPod networks: user VLANs on zcore, checked on zcore itself over SSH.

Every test drives `zcli zpod network ...` and then logs into zcore with the
factory key to check what really changed: the `eth1.<vlan>` interface and its
address (ifupdown file in /etc/network/interfaces.d), the masquerade rule in
nftables table `inet zboxapi`, the link state. A routed-VM test puts a zbox
on the user VLAN (an 802.1Q sub-interface over the zPod segment) and proves
zcore routes it, and that masquerade is what lets it reach the internet.

Edit E2E_USER_VLAN / E2E_USER_VLAN_GATEWAY (and E2E_SECOND_VLAN*) in .env if
10.42.111.0/24 or 10.42.112.0/24 collide with something in your lab.
"""

import ipaddress
import subprocess
import time

import httpx
import pytest

from e2e import status
from e2e.insight import Beat, Insight
from e2e.zssh import ZpodSsh

NET_NAME = "e2e-net"
SECOND_NET_NAME = "e2e-net2"
GLOBAL_NET_NAME = "e2e-global"
VLAN_VM_HOSTNAME = "e2e-vlanvm"
VLAN_VM_HOST_ID = 51
# zcore's own VLANs (nested VCF), never changed through zPodFactory.
ZCORE_VLANS = (10, 20, 30)

INSIGHTS = {
    "test_network_add_local_creates_vlan_interface": Insight(
        why="The API row is only bookkeeping: the network exists when zcore has an 802.1Q "
            "interface on the trunk NIC with the gateway address, and keeps it across a reboot.",
        reasoning="zboxapi writes /etc/network/interfaces.d/eth1.<vlan>.cfg and runs ifup. "
                  "Checking the live link (VLAN id, MTU 1700, address) and the file covers both "
                  "'works now' and 'comes back after reboot'.",
        expected="Row kind user / LOCAL / ACTIVE, `ip -d link` shows `vlan protocol 802.1Q id <vlan>`, "
                 "the gateway address is on it, the .cfg file exists, no masquerade rule.",
        beats=[
            Beat("zcli zpod network add", "local, masquerade off", state="ACTIVE", color="pass"),
            Beat("ssh zcore", "ip -d link / ip addr / interfaces.d", state="eth1.<vlan> up", color="pass", tag="ON HOST"),
        ],
    ),
    "test_network_masquerade_toggles_nftables_rule": Insight(
        why="Masquerade is a single nftables rule; a row saying `masquerade: true` while the rule "
            "is missing is the exact failure an operator can't see from zcli.",
        expected="On: rule `ip saddr <cidr> oifname \"eth0\" masquerade comment \"zboxapi vlan <id>\"` "
                 "in table inet zboxapi and persisted in /etc/nftables.d. Off: rule gone.",
    ),
    "test_vlan_vm_is_routed_by_zcore_and_masquerade_gates_internet": Insight(
        why="The point of a user VLAN is VMs on it: they must reach zcore, the zPod, and the "
            "internet only when masquerade is on (a LOCAL subnet has no route back from the fabric).",
        reasoning="A zbox gets an 802.1Q sub-interface for the VLAN over the zPod segment (the same "
                  "trunk zcore's eth1 is on) and a source-based route via the VLAN gateway, so its "
                  "management address keeps working for SSH.",
        beats=[
            Beat("zbox eth0.<vlan>", "10.42.111.51, default via zcore", state="ping gw", color="pass"),
            Beat("masquerade off", "curl internet from the VLAN address", state="fails", color="pass"),
            Beat("masquerade on", "same curl", state="HTTP answer", color="pass", tag="THE PROOF"),
        ],
    ),
}


def _networks(runner, zpod):
    return runner.run_json("zpod", "network", "list", zpod).json


def _network(runner, zpod, name):
    rows = _networks(runner, zpod)
    return next((r for r in rows if r["name"].lower() == name.lower()), None)


def _ifname(vlan: int) -> str:
    return f"eth1.{vlan}"


def _api(e2e_config, token: str | None = None) -> httpx.Client:
    return httpx.Client(
        base_url=e2e_config.api_base_url,
        headers={"access_token": token or e2e_config.superadmin_token},
        timeout=60,
    )


@pytest.fixture(scope="module")
def poll_network_routing(e2e_config):
    """Wait for a network's routing flow (PENDING) to end; returns the row."""

    def _poll(runner, zpod, name, timeout_seconds: int = 900):
        deadline = time.monotonic() + timeout_seconds
        while True:
            row = _network(runner, zpod, name)
            if row and row["routing"] != "PENDING" or time.monotonic() > deadline:
                return row
            time.sleep(e2e_config.poll_interval_seconds)

    return _poll


@pytest.fixture(scope="module")
def user_network(zcore_zpod, zcli_as, e2e_config, keep_resources):
    """The module's user VLAN (E2E_USER_VLAN), LOCAL, masquerade off - removed at the end."""
    runner = zcli_as("superadmin")
    runner(
        "zpod", "network", "add", zcore_zpod,
        "--name", NET_NAME,
        "--vlan", str(e2e_config.user_vlan),
        "--gateway", e2e_config.user_vlan_gateway,
    )
    yield NET_NAME
    if not keep_resources:
        runner("zpod", "network", "remove", zcore_zpod, NET_NAME, "-y", check=False)


# --------------------------------------------------------------------------
# Listing
# --------------------------------------------------------------------------


def test_network_list_shows_zpod_and_zcore_networks(zcli_as, zcore_zpod, zcore_ssh):
    """`zpod network list` shows the four deploy-time networks and zcore's own VLANs 10/20/30, which exist on zcore."""
    rows = _networks(zcli_as("superadmin"), zcore_zpod)
    zpod_rows = [r for r in rows if r["kind"] == "zpod"]
    zcore_rows = [r for r in rows if r["kind"] == "zcore"]

    assert len(zpod_rows) == 4, f"expected the 4 deploy-time networks (mgmt + 3 routed /26), got {zpod_rows}"
    assert sorted(r["vlan_id"] for r in zcore_rows) == list(ZCORE_VLANS), f"zcore VLANs: {zcore_rows}"

    links = zcore_ssh("ip -br link show").stdout
    for vlan in ZCORE_VLANS:
        assert f"{_ifname(vlan)}@eth1" in links, f"{_ifname(vlan)} missing on zcore:\n{links}"


def test_zcore_network_cannot_be_changed(zcli_as, zcore_zpod, e2e_config, api_check):
    """zcore's own VLANs are listed but refused for any change (403), not silently ignored."""
    zcore_row = next(r for r in _networks(zcli_as("superadmin"), zcore_zpod) if r["kind"] == "zcore")
    with _api(e2e_config) as api:
        resp = api.put(f"/zpods/name={zcore_zpod}/networks/{zcore_row['name']}/disable")
    api_check("PUT", "/zpods/{id}/networks/{name}/disable", "disable a zcore system VLAN",
              expected=403, actual=resp.status_code)
    assert resp.status_code == 403, f"expected 403, got {resp.status_code}: {resp.text}"


# --------------------------------------------------------------------------
# Add / masquerade / enable-disable, each proven on zcore
# --------------------------------------------------------------------------


def test_network_add_local_creates_vlan_interface(zcli_as, zcore_zpod, zcore_ssh, user_network, e2e_config):
    """Adding a LOCAL user network creates eth1.<vlan> on zcore with the gateway address, persisted in interfaces.d."""
    vlan, gateway = e2e_config.user_vlan, e2e_config.user_vlan_gateway
    row = _network(zcli_as("superadmin"), zcore_zpod, user_network)
    assert row, f"{user_network} not listed"
    assert row["kind"] == "user", f"kind: {row}"
    assert row["vlan_id"] == vlan, f"vlan: {row}"
    assert row["routing"] == "LOCAL", f"routing: {row}"
    assert row["masquerade"] is False, f"masquerade should default to off: {row}"
    assert row["status"] == "ACTIVE", f"status: {row}"
    assert row["cidr"] == str(ipaddress.ip_interface(gateway).network), f"cidr: {row}"

    link = zcore_ssh(f"ip -d link show {_ifname(vlan)}").stdout
    assert f"vlan protocol 802.1Q id {vlan}" in link, f"not an 802.1Q VLAN {vlan}:\n{link}"
    assert "mtu 1700" in link, f"expected MTU 1700 (zboxapi default):\n{link}"
    assert "state UP" in link or ",UP" in link, f"interface not up:\n{link}"

    addr = zcore_ssh(f"ip -4 -o addr show dev {_ifname(vlan)}").stdout
    assert gateway in addr, f"gateway {gateway} not on {_ifname(vlan)}:\n{addr}"

    cfg = zcore_ssh(f"cat /etc/network/interfaces.d/{_ifname(vlan)}.cfg").stdout
    assert f"auto {_ifname(vlan)}" in cfg and gateway in cfg, f"not persisted for reboot:\n{cfg}"

    nft = zcore_ssh("nft list table inet zboxapi 2>/dev/null || true").stdout
    assert f'zboxapi vlan {vlan}"' not in nft, f"masquerade rule present with masquerade off:\n{nft}"


def test_network_masquerade_toggles_nftables_rule(zcli_as, zcore_zpod, zcore_ssh, user_network, e2e_config):
    """Masquerade on adds the nftables rule for the VLAN's subnet (and persists it); off removes it."""
    runner = zcli_as("superadmin")
    vlan = e2e_config.user_vlan
    cidr = str(ipaddress.ip_interface(e2e_config.user_vlan_gateway).network)

    runner("zpod", "network", "masquerade", "on", zcore_zpod, user_network)
    assert _network(runner, zcore_zpod, user_network)["masquerade"] is True, "row not masquerade on"
    nft = zcore_ssh("nft list table inet zboxapi").stdout
    assert f"ip saddr {cidr}" in nft and "masquerade" in nft and f'comment "zboxapi vlan {vlan}"' in nft, (
        f"masquerade rule for {cidr} not found:\n{nft}"
    )
    persisted = zcore_ssh("cat /etc/nftables.d/zboxapi-masquerade.nft").stdout
    assert f"zboxapi vlan {vlan}" in persisted, f"rule not persisted:\n{persisted}"

    runner("zpod", "network", "masquerade", "off", zcore_zpod, user_network)
    assert _network(runner, zcore_zpod, user_network)["masquerade"] is False, "row not masquerade off"
    nft = zcore_ssh("nft list table inet zboxapi 2>/dev/null || true").stdout
    assert f"zboxapi vlan {vlan}" not in nft, f"rule still there after masquerade off:\n{nft}"


def test_network_disable_enable_toggles_link(zcli_as, zcore_zpod, zcore_ssh, user_network, e2e_config):
    """Disable brings eth1.<vlan> down on zcore (status DISABLED); enable brings it back up (ACTIVE)."""
    runner = zcli_as("superadmin")
    ifname = _ifname(e2e_config.user_vlan)

    runner("zpod", "network", "disable", zcore_zpod, user_network)
    assert _network(runner, zcore_zpod, user_network)["status"] == "DISABLED", "row not DISABLED"
    link = zcore_ssh(f"ip -br link show {ifname}").stdout
    assert link.split()[1] == "DOWN", f"{ifname} not down:\n{link}"

    runner("zpod", "network", "enable", zcore_zpod, user_network)
    assert _network(runner, zcore_zpod, user_network)["status"] == "ACTIVE", "row not ACTIVE"
    link = zcore_ssh(f"ip -br link show {ifname}").stdout
    assert link.split()[1] in ("UP", "UNKNOWN"), f"{ifname} not up:\n{link}"


# --------------------------------------------------------------------------
# Refusals - each with its status code, nothing created on zcore
# --------------------------------------------------------------------------


def _reject_cases(e2e_config, zpod_mgmt_cidr: str):
    mgmt_host = str(next(ipaddress.ip_network(zpod_mgmt_cidr).hosts()))
    prefix = ipaddress.ip_network(zpod_mgmt_cidr).prefixlen
    return [
        # refused by the API's own schema validation, before zcore is asked
        ("reserved zcore VLAN 10", {"name": "e2e-bad10", "vlan": 10, "gateway": e2e_config.second_vlan_gateway}, 422),
        ("VLAN already used", {"name": "e2e-dupvlan", "vlan": e2e_config.user_vlan, "gateway": e2e_config.second_vlan_gateway}, 409),
        ("name already used", {"name": NET_NAME, "vlan": e2e_config.second_vlan, "gateway": e2e_config.second_vlan_gateway}, 409),
        ("overlaps the zPod management network", {"name": "e2e-overlap", "vlan": e2e_config.second_vlan, "gateway": f"{mgmt_host}/{prefix}"}, 422),
        ("overlaps the first user network", {"name": "e2e-overlap2", "vlan": e2e_config.second_vlan, "gateway": e2e_config.user_vlan_gateway}, 422),
        ("VLAN out of range", {"name": "e2e-range", "vlan": 4095, "gateway": e2e_config.second_vlan_gateway}, 422),
    ]


def test_network_add_refusals(zcli_as, zcore_zpod, zcore_ssh, user_network, e2e_config, api_check):
    """Reserved VLANs, duplicates, overlapping subnets and out-of-range VLANs are refused with the right code, and leave zcore untouched."""
    rows = _networks(zcli_as("superadmin"), zcore_zpod)
    mgmt = next(r for r in rows if r["kind"] == "zpod")
    before = zcore_ssh("ls /etc/network/interfaces.d/").stdout

    failures = []
    with _api(e2e_config) as api:
        for label, body, expected in _reject_cases(e2e_config, mgmt["cidr"]):
            resp = api.post(f"/zpods/name={zcore_zpod}/networks", json=body)
            api_check("POST", "/zpods/{id}/networks", label, expected=expected, actual=resp.status_code,
                      note=resp.text[:200])
            if resp.status_code != expected:
                failures.append(f"{label}: expected {expected}, got {resp.status_code} {resp.text[:200]}")

    after = zcore_ssh("ls /etc/network/interfaces.d/").stdout
    assert not failures, "\n".join(failures)
    assert before == after, f"a refused add changed interfaces.d:\nbefore:\n{before}\nafter:\n{after}"


def test_global_routing_is_superadmin_only(zcore_zpod, user_network, _role_identities, e2e_config, api_check):
    """A non-superadmin can't change a network's routing: 403 from the superadmin-only route."""
    token = _role_identities["test_owner"]["token"]
    with _api(e2e_config, token) as api:
        resp = api.put(f"/zpods/name={zcore_zpod}/networks/{user_network}/routing", json={"routing": "GLOBAL"})
    api_check("PUT", "/zpods/{id}/networks/{name}/routing", "non-superadmin sets routing global",
              expected=403, actual=resp.status_code)
    assert resp.status_code == 403, f"expected 403, got {resp.status_code}: {resp.text}"


def test_global_routing_dry_run_changes_nothing(zcli_as, zcore_zpod, user_network):
    """`routing global --dry-run` runs the fabric checks and leaves the network LOCAL."""
    runner = zcli_as("superadmin")
    result = runner("zpod", "network", "routing", zcore_zpod, user_network, "global", "--dry-run",
                    check=False, timeout=600)
    assert result.returncode == 0, f"dry-run failed:\n{result.stdout}\n{result.stderr}"
    assert _network(runner, zcore_zpod, user_network)["routing"] == "LOCAL", "dry-run changed routing"


def _global_gateway(e2e_config, mgmt_cidr: str) -> str:
    """E2E_GLOBAL_VLAN_GATEWAY, or 192.168.<x>.1/24 with x the third octet of the
    zPod's own range: unique per zPod, so it can't collide with another zPod
    using the same scheme."""
    if e2e_config.global_vlan_gateway:
        return e2e_config.global_vlan_gateway
    x = ipaddress.ip_network(mgmt_cidr).network_address.packed[2]
    return f"192.168.{x}.1/24"


def _reachable(ip: str, *, want: bool, timeout_seconds: int = 90) -> bool:
    """Ping from the machine running the suite until reachability == want (routes take a moment)."""
    deadline = time.monotonic() + timeout_seconds
    while True:
        ok = subprocess.run(["ping", "-c2", "-W2", ip], capture_output=True).returncode == 0
        if ok == want or time.monotonic() > deadline:
            return ok
        time.sleep(5)


@pytest.mark.slow
def test_global_network_is_routed_by_the_fabric(zcli_as, zcore_zpod, zcore_ssh, e2e_config, poll_network_routing):
    """A network added as global is reachable from outside the zPod through NSX (zcore answers on it), can't be removed while global, and is withdrawn by routing local (opt-in: E2E_FABRIC_ROUTING)."""
    if not e2e_config.fabric_routing:
        pytest.skip("E2E_FABRIC_ROUTING is off - advertising a subnet into the NSX fabric is opt-in")
    runner = zcli_as("superadmin")
    mgmt = next(r for r in _networks(runner, zcore_zpod) if r["kind"] == "zpod")
    gateway = _global_gateway(e2e_config, mgmt["cidr"])
    gw_ip = str(ipaddress.ip_interface(gateway).ip)
    vlan = e2e_config.global_vlan

    if _reachable(gw_ip, want=True, timeout_seconds=0):
        pytest.skip(f"{gw_ip} already answers before the test - pick another E2E_GLOBAL_VLAN_GATEWAY")

    runner("zpod", "network", "add", zcore_zpod, "--name", GLOBAL_NET_NAME, "--vlan", str(vlan),
           "--gateway", gateway, "--routing", "global")
    try:
        row = poll_network_routing(runner, zcore_zpod, GLOBAL_NET_NAME)
        assert row["routing"] == "GLOBAL", f"advertise flow ended {row['routing']}: {row}"
        assert row["masquerade"] is False, f"a GLOBAL network has no masquerade: {row}"
        addr = zcore_ssh(f"ip -4 -o addr show dev {_ifname(vlan)}").stdout
        assert gateway in addr, f"{gateway} not on zcore's {_ifname(vlan)}:\n{addr}"

        assert _reachable(gw_ip, want=True), f"{gw_ip} not reachable from here once GLOBAL - not advertised?"
        via_fabric = ZpodSsh(host=gw_ip, key_path=zcore_ssh.key_path)
        assert via_fabric("hostname -s").stdout.strip() == "zcore", f"{gw_ip} answers, but it isn't this zcore"

        with _api(e2e_config) as api:
            resp = api.delete(f"/zpods/name={zcore_zpod}/networks/{GLOBAL_NET_NAME}")
        assert resp.status_code == 409, f"remove of a GLOBAL network: expected 409, got {resp.status_code}: {resp.text}"

        result = runner("zpod", "network", "routing", zcore_zpod, GLOBAL_NET_NAME, "local", check=False, timeout=900)
        assert result.returncode == 0, f"routing local failed:\n{result.stdout}"
        assert _network(runner, zcore_zpod, GLOBAL_NET_NAME)["routing"] == "LOCAL", "not back to LOCAL"
        assert not _reachable(gw_ip, want=False), f"{gw_ip} still reachable after routing local - route not withdrawn"
    finally:
        row = _network(runner, zcore_zpod, GLOBAL_NET_NAME)
        if row and row["routing"] == "GLOBAL":
            runner("zpod", "network", "routing", zcore_zpod, GLOBAL_NET_NAME, "local", check=False, timeout=900)
        if row:
            runner("zpod", "network", "remove", zcore_zpod, GLOBAL_NET_NAME, "-y", check=False)


# --------------------------------------------------------------------------
# A VM on the user VLAN, routed by zcore
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def vlan_vm(zcore_zpod, user_network, zcli_as, superadmin_client, zpod_ssh, poll_zpod_component_status, e2e_config, keep_resources):
    """A zbox on the zPod segment with an 802.1Q sub-interface on the user VLAN and a
    source route via zcore - its management address stays the SSH path."""
    components = superadmin_client.components_get_all.sync() or []
    if not any(c.component_uid == e2e_config.zbox_component_uid and c.status == "ACTIVE" for c in components):
        pytest.skip(f"{e2e_config.zbox_component_uid} not ACTIVE - enable it first")
    runner = zcli_as("superadmin")
    runner("zpod", "component", "add", zcore_zpod, "--component-uid", e2e_config.zbox_component_uid,
           "--hostname", VLAN_VM_HOSTNAME, "--host-id", str(VLAN_VM_HOST_ID), timeout=300)
    added = poll_zpod_component_status(superadmin_client, f"name={zcore_zpod}", f"hostname={VLAN_VM_HOSTNAME}")
    assert added.status == status.ZPOD_COMPONENT_ACTIVE, f"zbox add: {added.status}"

    vm = zpod_ssh(zcore_zpod, hostname=VLAN_VM_HOSTNAME)
    vm.wait_ready()
    gw = ipaddress.ip_interface(e2e_config.user_vlan_gateway)
    vm_ip = str(gw.network.network_address + VLAN_VM_HOST_ID)
    vlan = e2e_config.user_vlan
    vm(
        f"ip link add link eth0 name eth0.{vlan} type vlan id {vlan} && "
        f"ip addr add {vm_ip}/{gw.network.prefixlen} dev eth0.{vlan} && ip link set eth0.{vlan} up && "
        f"ip rule add from {vm_ip} table {vlan} && ip route add default via {gw.ip} table {vlan}"
    )
    yield vm, vm_ip

    if not keep_resources:
        runner("zpod", "component", "remove", zcore_zpod, VLAN_VM_HOSTNAME, "-y", check=False, timeout=300)


@pytest.mark.slow
def test_vlan_vm_is_routed_by_zcore_and_masquerade_gates_internet(zcli_as, zcore_zpod, zcore_ssh, user_network, vlan_vm, e2e_config):
    """A VM on the user VLAN reaches its zcore gateway and zcore's mgmt address; it reaches the internet only with masquerade on."""
    vm, vm_ip = vlan_vm
    runner = zcli_as("superadmin")
    gw_ip = str(ipaddress.ip_interface(e2e_config.user_vlan_gateway).ip)
    zcore_mgmt = zcore_ssh.host
    curl = f"curl -s -o /dev/null -m 10 -w '%{{http_code}}' --interface {vm_ip} {e2e_config.internet_probe_url}"

    assert vm(f"ping -c2 -W2 -I {vm_ip} {gw_ip}", check=False).ok, "VM can't reach its VLAN gateway on zcore"
    assert vm(f"ping -c2 -W2 -I {vm_ip} {zcore_mgmt}", check=False).ok, "zcore doesn't route VLAN -> zcore mgmt"
    seen = zcore_ssh(f"ip neigh show dev {_ifname(e2e_config.user_vlan)}").stdout
    assert vm_ip in seen, f"zcore never saw {vm_ip} on the VLAN (tagged frames not crossing the segment?):\n{seen}"

    runner("zpod", "network", "masquerade", "off", zcore_zpod, user_network)
    off = vm(curl, check=False).stdout.strip()
    assert off in ("", "000"), f"internet reachable with masquerade off (HTTP {off}) - is the subnet routed somewhere?"

    runner("zpod", "network", "masquerade", "on", zcore_zpod, user_network)
    try:
        on = vm(curl, check=False).stdout.strip()
        assert on and on != "000", f"internet not reachable from the VLAN with masquerade on (got '{on}')"
        conntrack = zcore_ssh(f"conntrack -L -s {vm_ip} 2>/dev/null | head -5 || true").stdout
        assert vm_ip in conntrack or conntrack == "", "unexpected conntrack output"
    finally:
        runner("zpod", "network", "masquerade", "off", zcore_zpod, user_network, check=False)


# --------------------------------------------------------------------------
# Remove - last, so the module's network is gone on zcore too
# --------------------------------------------------------------------------


def test_network_remove_cleans_zcore(zcli_as, zcore_zpod, zcore_ssh, e2e_config):
    """Adding then removing a second network deletes its interface, its interfaces.d file and any masquerade rule."""
    runner = zcli_as("superadmin")
    vlan = e2e_config.second_vlan
    runner("zpod", "network", "add", zcore_zpod, "--name", SECOND_NET_NAME, "--vlan", str(vlan),
           "--gateway", e2e_config.second_vlan_gateway, "--masquerade")
    assert f"zboxapi vlan {vlan}" in zcore_ssh("nft list table inet zboxapi").stdout, "added with --masquerade but no rule"

    runner("zpod", "network", "remove", zcore_zpod, SECOND_NET_NAME, "-y")
    assert _network(runner, zcore_zpod, SECOND_NET_NAME) is None, "still listed after remove"
    assert not zcore_ssh(f"test -e /etc/network/interfaces.d/{_ifname(vlan)}.cfg", check=False).ok, "cfg file left"
    assert not zcore_ssh(f"ip -4 -o addr show dev {_ifname(vlan)} 2>/dev/null | grep -q inet", check=False).ok, (
        "address still on zcore after remove"
    )
    nft = zcore_ssh("nft list table inet zboxapi 2>/dev/null || true").stdout
    assert f"zboxapi vlan {vlan}" not in nft, f"masquerade rule left behind:\n{nft}"
