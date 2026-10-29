"""The example profiles in tests/data/profiles: four that are accepted, one refused.

They show what a profile item can combine (nested, network, vlan_id, host_id) and
keep working as the rules change; the same files were created on a live factory.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from zpodcommon import models as M

PROFILES = Path(__file__).parent / "data" / "profiles"
MAPPING = {"NetworkMapping": [{"Name": "nic", "Network": "{{zpod_portgroup}}"}]}
ESXI = {
    **MAPPING,
    "PropertyMapping": [{"Key": "guestinfo.vlan", "Value": "{{zpod_vlan}}"}],
}
# uid: (component_name, component_isnested, govc spec), as in zPodLibrary
LIBRARY = {
    "zcore-13.7": ("zcore", False, MAPPING),
    "esxi-9.1.1.0": ("esxi", False, ESXI),
    "vcsa-9.1.1.0": ("vcsa", True, {}),
    "vcfinstaller-9.1.1.0": ("vcfinstaller", False, MAPPING),
    "nsx-4.2.4.1": ("nsx", True, MAPPING),
    "vrops-8.18.7": ("vrops", True, MAPPING),
    "vrli-8.18.7": ("vrli", True, MAPPING),
    "zbox-13.5": ("zbox", False, MAPPING),
    "ubuntu-24.04-dev": ("ubuntu", False, MAPPING),
    "photon-5.0-dev": ("photon", False, MAPPING),
    "talos-1.14.4-dev": ("talos", False, MAPPING),
    "flatcar-4757.2.2-dev": ("flatcar", False, MAPPING),
}


@pytest.fixture
def library(session: Session, tmp_path):
    for uid, (name, isnested, spec) in LIBRARY.items():
        jsonfile = tmp_path / f"{uid}.json"
        jsonfile.write_text(
            json.dumps(
                {
                    "component_name": name,
                    "component_isnested": isnested,
                    "component_deploy_govc_spec": spec,
                }
            )
        )
        session.add(
            M.Component(
                component_uid=uid,
                component_name=name,
                component_version=uid.split("-", 1)[1],
                component_description=name,
                filename=f"{uid}.ova",
                jsonfile=str(jsonfile),
                status="ACTIVE",
                download_status="COMPLETED",
                file_checksum="abc",
            )
        )
    session.commit()


def create(client: TestClient, name: str):
    profile = json.loads((PROFILES / f"{name}.json").read_text())
    return client.post("/profiles?force=false", json={"name": name, "profile": profile})


@pytest.mark.parametrize(
    "name", ["lab-vlan-mix", "endpoint-offload", "vcf-vlan64", "nested-apps"]
)
def test_example_profile_is_accepted(superadmin_client, library, name):
    response = create(superadmin_client, name)
    assert response.status_code == 201, response.text
    saved = response.json()["profile"]
    sent = json.loads((PROFILES / f"{name}.json").read_text())
    assert len(saved) == len(sent)


def test_example_profile_keeps_its_options(superadmin_client, library):
    saved = create(superadmin_client, "lab-vlan-mix").json()["profile"]
    hosts = {h["hostname"]: h for h in saved[1]}
    assert hosts["esxi71"]["vlan_id"] == 64
    assert hosts["esxi11"].get("vlan_id") is None
    assert saved[2]["nested"] is True  # vcsa stating its own default
    assert saved[3][1]["network"]["portgroup"] == "VM Network"


def test_broken_profile_lists_every_error(superadmin_client, library):
    response = create(superadmin_client, "broken")
    assert response.status_code == 400, response.text
    detail = response.json()["detail"]
    for line in [
        "esxi-9.1.1.0: host_id 60 is outside vlan64 (VLAN 64), which takes host_id 66 to 126",
        "vcsa-9.1.1.0: nested can't be set to false on vcsa: its placement is fixed",
        "zbox-13.5: network is only for nested components",
        "ubuntu-24.04-dev: network: ip gives the address, host_id can't be set with it",
        "vrops-8.18.7: vnics can't be set on a nested component",
        "zbox-13.5: host_id 53 is outside vlan64 (VLAN 64), which takes host_id 66 to 126",
        "zbox-13.5: vlan_id can't be set on zbox: its library JSON doesn't use {{zpod_vlan}}",
    ]:
        assert line in detail, f"missing: {line}\n{detail}"
