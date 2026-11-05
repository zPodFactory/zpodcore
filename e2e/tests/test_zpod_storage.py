"""zcore storage capabilities: disks, storages, folders and NFS exports, checked on zcore over SSH.

One lifecycle, in file order, on the shared zcore zPod: add a disk, make a
storage on it, add a folder, export it, mount the export, grow it online,
delete the storage and adopt it back with its data, then remove it with its
disk. After each `zcli zpod disk|storage|nfs ...` the test logs into zcore
with the factory key and checks the real thing: lsblk serial and size, the
partition table, the ext4 label, the systemd mount unit, findmnt, folder
mode/owner, /etc/exports.d/zboxapi.exports, `exportfs -v`, an actual NFS
mount writing a file, and that /etc/exports (zcore's own exports) is never
touched.

Sizes are tiny (2-3 GiB thin disks) so the module runs on any datastore.
"""

import json

import httpx
import pytest

from e2e.insight import Beat, Insight

DISK_GB = 2
GROW_GB = 3
DISK_GROW_GB = 4
FOLDER = "e2e-data"
FOLDER_MODE = "0755"
FOLDER_OWNER = "nobody:nogroup"
PROOF_FILE = "e2e-proof.txt"
PROOF_TEXT = "written over NFS by the e2e suite"
NFS_MOUNTPOINT = "/mnt/e2e-nfs"
SYSTEM_EXPORT = ("STORAGE01", "NFS-01")
GIB = 1024**3

INSIGHTS = {
    "test_storage_create_formats_and_mounts": Insight(
        why="A storage is a partition, an ext4 filesystem and a systemd mount unit that survives a "
            "reboot. zcli can list STORAGE02 while any one of those is missing.",
        expected="GPT with one partition, ext4 labelled STORAGE02, FILER-STORAGE02.mount enabled and "
                 "active, mounted on /FILER/STORAGE02 with noatime.",
        beats=[
            Beat("zcli zpod disk add", f"{DISK_GB} GiB thin", state="blank", color="pass"),
            Beat("zcli zpod storage create", "raw (no LVM)", state="STORAGE02", color="pass"),
            Beat("ssh zcore", "sfdisk / blkid / systemctl / findmnt", state="mounted", color="pass", tag="ON HOST"),
        ],
    ),
    "test_nfs_export_is_written_and_mountable": Insight(
        why="An export that is in the file but not live, or live but not mountable, looks the same "
            "in `nfs list`. Mounting it and writing a file is the only real proof.",
        reasoning="zcore mounts its own export over 127.0.0.1 (the export allows that client), writes a "
                  "file through NFS and the test reads it back from the storage path. `nfs status` "
                  "must then show the mounted client.",
        beats=[
            Beat("zcli zpod nfs add", "client 127.0.0.1", state="exported", color="pass"),
            Beat("mount -t nfs", "on zcore, loopback", state="file written", color="pass", tag="THE PROOF"),
            Beat("zcli zpod nfs status", "mounted clients", state="127.0.0.1", color="pass"),
        ],
    ),
    "test_storage_delete_then_adopt_keeps_data": Insight(
        why="`storage delete` promises the data stays on the disk and `adopt` brings it back. If "
            "either half lies, an operator loses data.",
        expected="After delete: not mounted, unit gone, filesystem still on the partition, disk "
                 "state foreign. After adopt: mounted again with the proof file intact.",
    ),
}


def _api(e2e_config) -> httpx.Client:
    return httpx.Client(base_url=e2e_config.api_base_url, headers={"access_token": e2e_config.superadmin_token}, timeout=120)


def _dev(device: str) -> str:
    return device if device.startswith("/dev/") else f"/dev/{device}"


def _disks(runner, zpod):
    return runner.run_json("zpod", "disk", "list", zpod).json


def _storages(runner, zpod):
    return runner.run_json("zpod", "storage", "list", zpod).json


def _storage(runner, zpod, name):
    return next((s for s in _storages(runner, zpod) if s["name"] == name), None)


def _exports(runner, zpod):
    return runner.run_json("zpod", "nfs", "list", zpod).json


def _serial(uuid: str | None) -> str:
    """vSphere backing.uuid as lsblk shows it with disk.EnableUUID=TRUE: no dashes, lowercase."""
    return (uuid or "").replace("-", "").lower()


@pytest.fixture(scope="module")
def runner(zcli_as):
    return zcli_as("superadmin")


@pytest.fixture(scope="module")
def etc_exports_sha(zcore_ssh):
    """zcore's own /etc/exports, hashed before the module touches anything."""
    return zcore_ssh("sha256sum /etc/exports").stdout.split()[0]


@pytest.fixture(scope="module")
def user_disk(zcore_zpod, runner, zcore_ssh, etc_exports_sha, keep_resources):
    """A DISK_GB GiB thin disk added to zcore, as listed by the API (dict)."""
    before = {d["device"] for d in _disks(runner, zcore_zpod)}
    runner("zpod", "disk", "add", zcore_zpod, "--size", str(DISK_GB), timeout=900)
    added = [d for d in _disks(runner, zcore_zpod) if d["kind"] == "user" and d["device"] not in before]
    assert len(added) == 1, f"expected one new user disk, got {added}"
    yield added[0]
    if not keep_resources:
        # The lifecycle's last test removes it; this only catches an early failure.
        for s in _storages(runner, zcore_zpod):
            if s.get("kind") == "user" and s["device"].startswith(_dev(added[0]["device"])):
                runner("zpod", "storage", "remove", zcore_zpod, s["name"], "-y", check=False, timeout=900)
        if any(d["device"] == added[0]["device"] for d in _disks(runner, zcore_zpod)):
            runner("zpod", "disk", "remove", zcore_zpod, _dev(added[0]["device"]), "-y", check=False, timeout=900)


# --------------------------------------------------------------------------
# Disks
# --------------------------------------------------------------------------


def test_disk_list_shows_zpod_disks_with_serials(zcore_zpod, runner, zcore_ssh):
    """The two deploy-time disks are listed (kind zpod) and zcore sees each with the serial of its vSphere disk (disk.EnableUUID)."""
    zpod_disks = [d for d in _disks(runner, zcore_zpod) if d["kind"] == "zpod"]
    assert len(zpod_disks) == 2, f"expected system + filer disks, got {zpod_disks}"
    for d in zpod_disks:
        serial = zcore_ssh(f"lsblk -dno SERIAL {_dev(d['device'])}").stdout.strip().lower()
        assert serial, f"{d['device']} has no serial on zcore - disk.EnableUUID not set on the VM"
        if d.get("disk_uuid"):
            assert serial == _serial(d["disk_uuid"]), f"{d['device']}: lsblk serial {serial} != disk_uuid {d['disk_uuid']}"


def test_disk_add_attaches_blank_disk(zcore_zpod, user_disk, zcore_ssh):
    """`zpod disk add` attaches a thin disk zcore sees at the asked size, blank, matched by serial."""
    dev = _dev(user_disk["device"])
    assert user_disk["size_gb"] == DISK_GB, f"size: {user_disk}"
    assert user_disk["status"] == "ACTIVE", f"status: {user_disk}"
    assert user_disk["state"] == "blank", f"state: {user_disk}"

    size, serial = zcore_ssh(f"lsblk -dbno SIZE,SERIAL {dev}").stdout.split()
    assert int(size) == DISK_GB * GIB, f"zcore sees {size} bytes on {dev}, expected {DISK_GB} GiB"
    assert serial.lower() == _serial(user_disk["disk_uuid"]), f"serial {serial} != disk_uuid {user_disk['disk_uuid']}"
    parts = zcore_ssh(f"lsblk -nro NAME {dev} | wc -l").stdout.strip()
    assert parts == "1", f"{dev} is not blank (has children):\n{zcore_ssh(f'lsblk {dev}').stdout}"


# --------------------------------------------------------------------------
# Storage on that disk
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def user_storage(zcore_zpod, user_disk, runner):
    """The storage created on user_disk (raw): its name (STORAGE02 on a fresh zcore)."""
    before = {s["name"] for s in _storages(runner, zcore_zpod)}
    runner("zpod", "storage", "create", zcore_zpod, "--disk", _dev(user_disk["device"]), timeout=600)
    created = [s for s in _storages(runner, zcore_zpod) if s["name"] not in before]
    assert len(created) == 1, f"expected one new storage, got {created}"
    return created[0]["name"]


def test_storage_create_formats_and_mounts(zcore_zpod, user_disk, user_storage, runner, zcore_ssh):
    """`zpod storage create` partitions (GPT), formats ext4 labelled with the name, and mounts it via an enabled systemd unit."""
    dev = _dev(user_disk["device"])
    part = f"{dev}1"
    mount = f"/FILER/{user_storage}"
    unit = f"FILER-{user_storage}.mount"

    s = _storage(runner, zcore_zpod, user_storage)
    assert s["kind"] == "user" and s["managed"] is True and s["protected"] is False, f"storage row: {s}"

    table = zcore_ssh(f"sfdisk -d {dev}").stdout
    assert "label: gpt" in table and table.count(f"{part} :") == 1, f"not one GPT partition:\n{table}"
    label = zcore_ssh(f"blkid -s LABEL -o value {part}").stdout.strip()
    fstype = zcore_ssh(f"blkid -s TYPE -o value {part}").stdout.strip()
    assert (label, fstype) == (user_storage, "ext4"), f"blkid: label={label} type={fstype}"

    assert zcore_ssh(f"systemctl is-enabled {unit}").stdout.strip() == "enabled", f"{unit} not enabled (no reboot persistence)"
    assert zcore_ssh(f"systemctl is-active {unit}").stdout.strip() == "active", f"{unit} not active"
    src, fs, opts = zcore_ssh(f"findmnt -no SOURCE,FSTYPE,OPTIONS {mount}").stdout.split()
    assert src == part and fs == "ext4" and "noatime" in opts, f"findmnt {mount}: {src} {fs} {opts}"
    assert not zcore_ssh(f"grep -q '{mount}' /etc/fstab", check=False).ok, "a user storage must not be in /etc/fstab"

    disk = next(d for d in _disks(runner, zcore_zpod) if d["device"] == user_disk["device"])
    assert disk["storage"] == user_storage and disk["state"] == "in-use", f"disk row after create: {disk}"


def test_storage_folder_add_sets_owner_and_mode(zcore_zpod, user_storage, runner, zcore_ssh):
    """`zpod storage folder add` creates the folder with the asked owner and mode."""
    runner("zpod", "storage", "folder", "add", zcore_zpod, user_storage, FOLDER,
           "--owner", FOLDER_OWNER, "--mode", FOLDER_MODE)
    mode_owner = zcore_ssh(f"stat -c '%a %U:%G' /FILER/{user_storage}/{FOLDER}").stdout.strip()
    assert mode_owner == f"{FOLDER_MODE.lstrip('0')} {FOLDER_OWNER}", f"stat: {mode_owner}"
    folders = _storage(runner, zcore_zpod, user_storage)["folders"]
    assert any(f["name"] == FOLDER and f["exported"] is False for f in folders), f"folders: {folders}"

    # back to the default, so NFS clients mapped to root (no_root_squash) and nobody can both write
    runner("zpod", "storage", "folder", "set", zcore_zpod, user_storage, FOLDER, "--mode", "0777", check=False)


# --------------------------------------------------------------------------
# NFS
# --------------------------------------------------------------------------


@pytest.fixture
def nfs_mount(zcore_ssh, user_storage):
    """Unmounts the loopback NFS mount whatever the test did."""
    yield NFS_MOUNTPOINT
    zcore_ssh(f"umount -f {NFS_MOUNTPOINT} 2>/dev/null; rmdir {NFS_MOUNTPOINT} 2>/dev/null; true", check=False)


def test_nfs_export_is_written_and_mountable(zcore_zpod, user_storage, runner, zcore_ssh, nfs_mount, etc_exports_sha):
    """`zpod nfs add` writes the export to /etc/exports.d, makes it live, and a client can mount it and write a file."""
    path = f"/FILER/{user_storage}/{FOLDER}"
    runner("zpod", "nfs", "add", zcore_zpod, user_storage, FOLDER, "-c", "127.0.0.1")

    managed = zcore_ssh("cat /etc/exports.d/zboxapi.exports").stdout
    assert f"{path} 127.0.0.1(rw,no_subtree_check,no_root_squash)" in managed, f"export line:\n{managed}"
    live = zcore_ssh("exportfs -v").stdout
    assert path in live and "127.0.0.1" in live, f"not live in exportfs:\n{live}"
    exp = next((e for e in _exports(runner, zcore_zpod) if e["path"] == path), None)
    assert exp and exp["active"] is True and [c["client"] for c in exp["clients"]] == ["127.0.0.1"], f"nfs list: {exp}"

    zcore_ssh(f"mkdir -p {nfs_mount} && mount -t nfs -o vers=4.2,soft,timeo=50 127.0.0.1:{path} {nfs_mount}", timeout=90)
    zcore_ssh(f"echo '{PROOF_TEXT}' > {nfs_mount}/{PROOF_FILE} && sync")
    on_disk = zcore_ssh(f"cat {path}/{PROOF_FILE}").stdout.strip()
    assert on_disk == PROOF_TEXT, f"file written over NFS reads back as '{on_disk}'"

    status_json = runner.run_json("zpod", "nfs", "status", zcore_zpod).json
    assert status_json["enabled"] is True, f"nfs status: {status_json}"
    assert "127.0.0.1" in json.dumps(status_json["clients"]), f"mounted client not reported: {status_json}"

    zcore_ssh(f"umount {nfs_mount}")
    assert zcore_ssh("sha256sum /etc/exports").stdout.split()[0] == etc_exports_sha, "/etc/exports was modified"


def test_nfs_clients_add_remove_and_set(zcore_zpod, user_storage, runner, zcore_ssh, e2e_config):
    """Client add/remove change the live export; `nfs set` replaces clients and options exactly."""
    path = f"/FILER/{user_storage}/{FOLDER}"
    subnet = e2e_config.user_vlan_gateway.rsplit(".", 1)[0] + ".0/" + e2e_config.user_vlan_gateway.split("/")[1]

    runner("zpod", "nfs", "client", "add", zcore_zpod, user_storage, FOLDER, subnet)
    assert subnet in zcore_ssh("cat /etc/exports.d/zboxapi.exports").stdout, f"{subnet} not added"
    assert subnet in zcore_ssh("exportfs -v").stdout, f"{subnet} not live"

    runner("zpod", "nfs", "client", "remove", zcore_zpod, user_storage, FOLDER, subnet)
    assert subnet not in zcore_ssh("cat /etc/exports.d/zboxapi.exports").stdout, f"{subnet} not removed"

    runner("zpod", "nfs", "set", zcore_zpod, user_storage, FOLDER, "-c", "127.0.0.1", "-c", subnet,
           "-o", "ro,no_subtree_check,root_squash")
    line = next(ln for ln in zcore_ssh("cat /etc/exports.d/zboxapi.exports").stdout.splitlines() if ln.startswith(path))
    assert line == f"{path} 127.0.0.1(ro,no_subtree_check,root_squash) {subnet}(ro,no_subtree_check,root_squash)", (
        f"nfs set didn't produce exactly the asked export:\n{line}"
    )
    # back to rw for the rest of the lifecycle
    runner("zpod", "nfs", "set", zcore_zpod, user_storage, FOLDER, "-c", "127.0.0.1",
           "-o", "rw,no_subtree_check,no_root_squash")


def test_exported_folder_and_storage_are_protected(zcore_zpod, user_storage, runner, zcore_ssh, e2e_config, api_check):
    """An exported folder can't be removed and a storage with exports can't be deleted (409); the data stays."""
    with _api(e2e_config) as api:
        resp = api.delete(f"/zpods/name={zcore_zpod}/storages/{user_storage}/folders/{FOLDER}", params={"force": True})
        api_check("DELETE", "/zpods/{id}/storages/{name}/folders/{folder}", "remove an exported folder (force)",
                  expected=409, actual=resp.status_code, note=resp.text[:200])
        assert resp.status_code == 409, f"expected 409, got {resp.status_code}: {resp.text}"

        resp = api.delete(f"/zpods/name={zcore_zpod}/storages/{user_storage}")
        api_check("DELETE", "/zpods/{id}/storages/{name}", "delete a storage that has an export",
                  expected=409, actual=resp.status_code, note=resp.text[:200])
        assert resp.status_code == 409, f"expected 409, got {resp.status_code}: {resp.text}"

    assert zcore_ssh(f"test -f /FILER/{user_storage}/{FOLDER}/{PROOF_FILE}", check=False).ok, "data gone after refusals"


def test_zcore_own_storage_and_exports_are_protected(zcore_zpod, runner, zcore_ssh, e2e_config, etc_exports_sha, api_check):
    """STORAGE01, its system export NFS-01 and the filer disk are refused (403), and /etc/exports stays byte-identical."""
    storage, folder = SYSTEM_EXPORT
    zpod_disks = [d for d in _disks(runner, zcore_zpod) if d["kind"] == "zpod"]
    # the filer disk is the deploy-time disk STORAGE01 lives on (SCSI 0:1), never the system disk
    filer = next((d for d in zpod_disks if d.get("storage") == storage), zpod_disks[-1])
    cases = [
        ("delete", f"/zpods/name={zcore_zpod}/storages/{storage}", "delete STORAGE01"),
        ("delete", f"/zpods/name={zcore_zpod}/nfs/{storage}/{folder}", "remove the system export NFS-01"),
        ("delete", f"/zpods/name={zcore_zpod}/disks/{filer['device'].removeprefix('/dev/')}", "remove the filer disk"),
    ]
    failures = []
    with _api(e2e_config) as api:
        for method, url, label in cases:
            resp = api.request(method.upper(), url)
            api_check(method.upper(), url.replace(zcore_zpod, "{zpod}"), label, expected=403, actual=resp.status_code,
                      note=resp.text[:200])
            if resp.status_code != 403:
                failures.append(f"{label}: expected 403, got {resp.status_code} {resp.text[:200]}")
    assert not failures, "\n".join(failures)
    assert zcore_ssh("sha256sum /etc/exports").stdout.split()[0] == etc_exports_sha, "/etc/exports was modified"
    assert zcore_ssh(f"findmnt /FILER/{storage}", check=False).ok, "STORAGE01 no longer mounted"


def test_disk_add_above_cap_is_refused(zcore_zpod, zcli_as, superadmin_client, _role_identities, e2e_config, api_check):
    """A zPod owner asking for a disk above zpodfactory_zpod_disk_max_gb gets 422 before anything is created.

    Superadmins are exempt from the cap by design, so this runs as test_owner,
    granted owner on the shared zPod for the duration of the test.
    """
    settings = superadmin_client.settings_get_all.sync() or []
    cap = next((s.value for s in settings if s.name == "zpodfactory_zpod_disk_max_gb"), None)
    if not cap:
        pytest.skip("zpodfactory_zpod_disk_max_gb not set on this server")
    owner = _role_identities["test_owner"]
    admin = zcli_as("superadmin")
    admin("zpod", "permission", "add", zcore_zpod, "-p", "owner", "-u", owner["username"])
    try:
        api = httpx.Client(base_url=e2e_config.api_base_url, headers={"access_token": owner["token"]}, timeout=60)
        with api:
            resp = api.post(f"/zpods/name={zcore_zpod}/disks", json={"size_gb": int(cap) + 1})
        api_check("POST", "/zpods/{id}/disks", f"zPod owner asks {int(cap) + 1} GiB (cap {cap})",
                  expected=422, actual=resp.status_code, note=resp.text[:200])
        assert resp.status_code == 422, f"expected 422, got {resp.status_code}: {resp.text}"
    finally:
        admin("zpod", "permission", "remove", zcore_zpod, "-p", "owner", "-u", owner["username"], check=False)


def test_disk_remove_in_use_is_refused(zcore_zpod, user_disk, user_storage, runner, zcore_ssh):
    """Removing a disk that backs a mounted storage is refused, and the storage stays mounted."""
    result = runner("zpod", "disk", "remove", zcore_zpod, _dev(user_disk["device"]), "-y", check=False, timeout=300)
    assert result.returncode != 0, f"disk remove of an in-use disk succeeded:\n{result.stdout}"
    assert zcore_ssh(f"findmnt /FILER/{user_storage}", check=False).ok, f"{user_storage} unmounted by a refused remove"


# --------------------------------------------------------------------------
# Grow, delete + adopt, remove
# --------------------------------------------------------------------------


def test_storage_grow_is_online(zcore_zpod, user_disk, user_storage, runner, zcore_ssh):
    """`storage grow --size` grows the disk, the partition and ext4 online; the data stays readable."""
    dev = _dev(user_disk["device"])
    mount = f"/FILER/{user_storage}"
    fs_before = int(zcore_ssh(f"df -B1 --output=size {mount} | tail -1").stdout)

    runner("zpod", "storage", "grow", zcore_zpod, user_storage, "--size", str(GROW_GB), timeout=900)

    assert int(zcore_ssh(f"lsblk -dbno SIZE {dev}").stdout) == GROW_GB * GIB, "disk not grown on zcore"
    assert int(zcore_ssh(f"lsblk -bno SIZE {dev}1").stdout) > (DISK_GB * GIB), "partition not grown"
    fs_after = int(zcore_ssh(f"df -B1 --output=size {mount} | tail -1").stdout)
    assert fs_after > fs_before, f"filesystem not grown: {fs_before} -> {fs_after}"
    assert zcore_ssh(f"cat {mount}/{FOLDER}/{PROOF_FILE}").stdout.strip() == PROOF_TEXT, "data lost by grow"
    disk = next(d for d in _disks(runner, zcore_zpod) if d["device"] == user_disk["device"])
    assert disk["size_gb"] == GROW_GB, f"disk row not updated: {disk}"


def test_disk_grow_grows_the_disk_only(zcore_zpod, user_disk, user_storage, runner, zcore_ssh, e2e_config, api_check):
    """`disk grow --size` grows the vSphere disk only (the partition and the storage stay as they are); a size that isn't larger, or zcore's own disk, is refused."""
    dev = _dev(user_disk["device"])
    part_before = int(zcore_ssh(f"lsblk -bno SIZE {dev}1").stdout)

    runner("zpod", "disk", "grow", zcore_zpod, dev, "--size", str(DISK_GROW_GB), timeout=900)

    assert int(zcore_ssh(f"lsblk -dbno SIZE {dev}").stdout) == DISK_GROW_GB * GIB, "disk not grown on zcore"
    assert int(zcore_ssh(f"lsblk -bno SIZE {dev}1").stdout) == part_before, "disk grow touched the partition"
    assert zcore_ssh(f"cat /FILER/{user_storage}/{FOLDER}/{PROOF_FILE}").stdout.strip() == PROOF_TEXT, "data lost"
    disk = next(d for d in _disks(runner, zcore_zpod) if d["device"] == user_disk["device"])
    assert disk["size_gb"] == DISK_GROW_GB, f"disk row not updated: {disk}"

    with httpx.Client(base_url=e2e_config.api_base_url, headers={"access_token": e2e_config.superadmin_token},
                      timeout=60) as api:
        resp = api.put(f"/zpods/name={zcore_zpod}/disks/{dev.removeprefix('/dev/')}/grow", json={"size_gb": DISK_GROW_GB})
        api_check("PUT", "/zpods/{id}/disks/{device}/grow", "same size again", expected=422, actual=resp.status_code,
                  note=resp.text[:200])
        assert resp.status_code == 422, f"{resp.status_code}: {resp.text}"
        system = next(d for d in _disks(runner, zcore_zpod) if d["kind"] == "zpod")
        resp = api.put(f"/zpods/name={zcore_zpod}/disks/{_dev(system['device']).removeprefix('/dev/')}/grow",
                       json={"size_gb": system["size_gb"] + 1})  # +1 GiB: harmless if it were ever accepted
        api_check("PUT", "/zpods/{id}/disks/{device}/grow", "zcore's own disk", expected=403, actual=resp.status_code,
                  note=resp.text[:200])
        assert resp.status_code == 403, f"{resp.status_code}: {resp.text}"


def test_storage_delete_then_adopt_keeps_data(zcore_zpod, user_disk, user_storage, runner, zcore_ssh):
    """Delete unmounts and drops the unit but keeps the filesystem; adopt mounts it back with the data intact."""
    dev = _dev(user_disk["device"])
    part = f"{dev}1"
    mount = f"/FILER/{user_storage}"
    unit = f"/etc/systemd/system/FILER-{user_storage}.mount"

    runner("zpod", "nfs", "remove", zcore_zpod, user_storage, FOLDER, "-y")
    assert f"/FILER/{user_storage}/{FOLDER}" not in zcore_ssh("exportfs -v").stdout, "export still live"

    runner("zpod", "storage", "delete", zcore_zpod, user_storage, timeout=300)
    assert not zcore_ssh(f"findmnt {mount}", check=False).ok, f"{mount} still mounted after delete"
    assert not zcore_ssh(f"test -e {unit}", check=False).ok, "mount unit left behind"
    assert zcore_ssh(f"blkid -s TYPE -o value {part}").stdout.strip() == "ext4", "filesystem gone after delete"
    disk = next(d for d in _disks(runner, zcore_zpod) if d["device"] == user_disk["device"])
    assert disk["state"] == "foreign", f"disk state after delete: {disk}"

    runner("zpod", "storage", "adopt", zcore_zpod, "--device", part, "--name", user_storage, timeout=300)
    assert zcore_ssh(f"findmnt {mount}", check=False).ok, f"{mount} not mounted after adopt"
    assert zcore_ssh(f"cat {mount}/{FOLDER}/{PROOF_FILE}").stdout.strip() == PROOF_TEXT, "data lost across delete+adopt"


def test_storage_remove_deletes_disk(zcore_zpod, user_disk, user_storage, runner, zcore_ssh):
    """`storage remove` unmounts, drops the unit and detaches the disk: zcore no longer has a disk with that serial."""
    serial = _serial(user_disk["disk_uuid"])
    runner("zpod", "storage", "remove", zcore_zpod, user_storage, "-y", timeout=900)

    assert _storage(runner, zcore_zpod, user_storage) is None, "storage still listed"
    assert not any(d["device"] == user_disk["device"] for d in _disks(runner, zcore_zpod) if d["kind"] == "user"), "disk still listed"
    serials = zcore_ssh("lsblk -dno SERIAL").stdout.lower().split()
    assert serial not in serials, f"zcore still sees the disk (serial {serial})"
    assert not zcore_ssh(f"test -e /etc/systemd/system/FILER-{user_storage}.mount", check=False).ok, "unit left behind"


def test_storage_add_lvm_one_command(zcore_zpod, runner, zcore_ssh, keep_resources):
    """`storage add --lvm` adds a disk and builds PV/VG/LV + ext4 on it in one command; `storage remove` undoes all of it."""
    before = {s["name"] for s in _storages(runner, zcore_zpod)}
    runner("zpod", "storage", "add", zcore_zpod, "--size", str(DISK_GB), "--lvm", timeout=900)
    created = [s for s in _storages(runner, zcore_zpod) if s["name"] not in before]
    assert len(created) == 1, f"expected one new storage, got {created}"
    name = created[0]["name"]
    vg = f"vg_{name.lower()}"
    try:
        assert created[0]["vg"] == vg and created[0]["lv"] == "data", f"storage row: {created[0]}"
        assert zcore_ssh(f"vgs --noheadings -o vg_name {vg}").stdout.strip() == vg, f"no VG {vg}"
        assert zcore_ssh(f"lvs --noheadings -o lv_name {vg}/data").stdout.strip() == "data", "no LV data"
        src = zcore_ssh(f"findmnt -no SOURCE /FILER/{name}").stdout.strip()
        assert src == f"/dev/mapper/{vg}-data", f"mounted from {src}"
    finally:
        if not keep_resources:
            runner("zpod", "storage", "remove", zcore_zpod, name, "-y", check=False, timeout=900)
    if not keep_resources:
        assert not zcore_ssh(f"vgs {vg}", check=False).ok, f"VG {vg} left behind"
