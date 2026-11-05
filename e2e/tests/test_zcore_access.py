"""zcore of a fresh zPod, from the inside: key login, zboxapi, DNS, filer and NFS baseline.

The network and storage modules assume a zcore that zPodFactory can drive:
key-based root login, zboxapi recent enough for networks and storages,
STORAGE01 mounted and exported. This module checks that baseline first, so a
wrong zcore image fails here with one clear message instead of as twenty
confusing failures later.
"""

import json

import pytest

from e2e.insight import Beat, Insight

# zPodFactory refuses disk/storage/NFS calls (501) below this zboxapi version.
MIN_ZBOXAPI = (0, 2, 1)

INSIGHTS = {
    "test_zcore_accepts_factory_key_only": Insight(
        why="Every on-host check in the suite relies on the factory key reaching zcore through the "
            "deploy (guestinfo.sshkey). If that injection breaks, nobody notices until they need "
            "to log in - and the zPod's password still works, hiding the problem.",
        reasoning="SSH with BatchMode=yes and IdentitiesOnly: no password fallback is possible, so "
                  "a login proves the key was injected; the key is also checked in authorized_keys.",
        beats=[
            Beat("zpodfactory_ssh_key", "setting on the server", state="matches E2E_ZPOD_SSH_KEY", color="pass"),
            Beat("ssh root@zcore", "BatchMode, key only", state="logged in", color="pass", tag="THE PROOF"),
        ],
    ),
}


def _version_tuple(text: str) -> tuple[int, ...]:
    return tuple(int(p) for p in text.split("+")[0].split("-")[0].split(".")[:3])


@pytest.mark.smoke
def test_zcore_accepts_factory_key_only(zcore_ssh, zpod_ssh_key):
    """root on zcore logs in with the factory key (no password possible), and the key is in authorized_keys."""
    from e2e.zssh import public_key_of

    assert zcore_ssh("id -un").stdout.strip() == "root", "not logged in as root"
    keys = zcore_ssh("cat /root/.ssh/authorized_keys").stdout
    assert public_key_of(zpod_ssh_key) in keys, "factory public key not in zcore's authorized_keys"


def test_zcore_identity_matches_api(zcore_zpod, zcore_ssh, superadmin_client):
    """zcore's hostname and FQDN are the ones the API reports, and zcore resolves its own FQDN."""
    components = superadmin_client.zpods_components_get_all.sync(id=f"name={zcore_zpod}") or []
    zcore = next(c for c in components if c.hostname == "zcore")
    assert zcore_ssh("hostname -s").stdout.strip() == "zcore", "short hostname"
    assert zcore_ssh("hostname -f").stdout.strip() == zcore.fqdn, f"FQDN != API's {zcore.fqdn}"
    resolved = zcore_ssh(f"getent hosts {zcore.fqdn}").stdout.split()
    assert resolved and resolved[0] == zcore.ip, f"zcore resolves {zcore.fqdn} to {resolved}, API says {zcore.ip}"


def test_zboxapi_version_supports_selfservice(zcore_ssh):
    """zboxapi on zcore is recent enough for networks, disks, storages and NFS (>= 0.2.1)."""
    raw = zcore_ssh("curl -sf http://127.0.0.1:8000/openapi.json").stdout
    version = json.loads(raw)["info"]["version"]
    assert _version_tuple(version) >= MIN_ZBOXAPI, (
        f"zboxapi {version} < {'.'.join(map(str, MIN_ZBOXAPI))}: deploy a newer zcore (E2E_ZCORE_COMPONENT_UID)"
    )
    assert zcore_ssh("systemctl is-active zboxapi", check=False).stdout.strip() == "active", "zboxapi service not active"


def test_zcore_filer_and_nfs_baseline(zcore_ssh):
    """STORAGE01 is mounted from /etc/fstab, nfs-server is active and /etc/exports holds the system exports."""
    assert zcore_ssh("findmnt -no TARGET /FILER/STORAGE01").stdout.strip() == "/FILER/STORAGE01", "STORAGE01 not mounted"
    assert zcore_ssh("systemctl is-active nfs-server").stdout.strip() == "active", "nfs-server not active"
    exports = zcore_ssh("cat /etc/exports").stdout
    assert "/FILER/STORAGE01/NFS-01" in exports, f"system export NFS-01 missing:\n{exports}"
    assert "/FILER/STORAGE01/NFS-01" in zcore_ssh("exportfs -v").stdout, "NFS-01 not live"


def test_zcore_has_nftables_and_forwarding(zcore_ssh):
    """zcore forwards IPv4 (it is every zPod VLAN's router) and has nftables to masquerade with."""
    assert zcore_ssh("sysctl -n net.ipv4.ip_forward").stdout.strip() == "1", "IPv4 forwarding off on zcore"
    assert zcore_ssh("command -v nft", check=False).ok, "nft not installed on zcore"
    assert "include" in zcore_ssh("cat /etc/nftables.conf").stdout, (
        "/etc/nftables.conf doesn't include /etc/nftables.d - masquerade rules won't survive a reboot"
    )


def test_zpod_info_panels_render(zcli_as, zcore_zpod):
    """`zpod info` renders its Storage and DNS panels for a zcore zPod (screenshots in the report)."""
    runner = zcli_as("superadmin")
    storage = runner("zpod", "info", zcore_zpod, "-f", "s")
    assert storage.returncode == 0 and "STORAGE01" in storage.stdout, f"storage panel:\n{storage.stdout}"
    dns_panel = runner("zpod", "info", zcore_zpod, "-f", "d")
    assert dns_panel.returncode == 0 and "zcore" in dns_panel.stdout, f"DNS panel:\n{dns_panel.stdout}"
