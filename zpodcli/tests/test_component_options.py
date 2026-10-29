"""zcli zpod component add: --nested, the network options and --vlan-id reach the
request as the API expects them; zcli profile list shows them."""

import pytest
from typer.testing import CliRunner

import zpodcli.cmd.zpod_component_cli as component_cli
from zpodcli.cmd.profile_cli import profile_item_output
from zpodsdk.models.component_network_spec import ComponentNetworkSpec
from zpodsdk.models.profile_item_view import ProfileItemView

runner = CliRunner()


@pytest.fixture
def sent(monkeypatch):
    bodies = []

    class FakeClient:
        def __init__(self):
            self.zpods_components_add = self

        def sync(self, id, body):
            bodies.append(body.to_dict())

    monkeypatch.setattr(component_cli, "ZpodClient", FakeClient)
    return bodies


def add(*args):
    return runner.invoke(
        component_cli.app, ["add", "demo", "-c", "ubuntu-24.04", *args]
    )


@pytest.mark.parametrize(
    "args, nested",
    [
        (["--nested=true"], True),
        (["--nested", "false"], False),
        (["--nested=TRUE"], True),
        ([], None),
    ],
)
def test_nested(sent, args, nested):
    assert add(*args).exit_code == 0
    assert sent[-1]["nested"] is nested


def test_nested_takes_only_true_or_false(sent):
    result = add("--nested=yes")
    assert result.exit_code == 2
    assert sent == []


def test_network_options(sent):
    result = add(
        "--nested=true",
        "--hostname",
        "jump01",
        "--ip",
        "10.96.1.50/26",
        "--gateway",
        "10.96.1.1",
        "--dns",
        "10.96.1.2",
        "--portgroup",
        "VM Network",
    )
    assert result.exit_code == 0, result.output
    assert sent[-1]["network"] == {
        "ip": "10.96.1.50/26",
        "gateway": "10.96.1.1",
        "dns": "10.96.1.2",
        "portgroup": "VM Network",
    }
    assert sent[-1]["hostname"] == "jump01"


def test_portgroup_and_host_id(sent):
    # The portgroup's VLAN picks the network --host-id is on: no --zpod-network.
    assert add("--nested=true", "--portgroup", "PG64", "--host-id", "74").exit_code == 0
    assert sent[-1]["network"] == {"portgroup": "PG64"}
    assert sent[-1]["host_id"] == 74
    assert add("--nested=true", "--zpod-network", "vlan64").exit_code == 2


def test_no_network_options_send_no_network(sent):
    assert add().exit_code == 0
    assert sent[-1]["network"] is None


def test_vlan_id(sent):
    assert add("--host-id", "71", "--vlan-id", "64").exit_code == 0
    assert sent[-1]["vlan_id"] == 64
    assert add("--host-id", "71", "--vlan_id=64").exit_code == 2  # dashes only


def test_profile_list_shows_the_options():
    profile = type(
        "P",
        (),
        {
            "profile": [
                ProfileItemView(component_uid="esxi-9", host_id=71, vlan_id=64),
                ProfileItemView(component_uid="vcsa-9", nested=True),
                ProfileItemView(component_uid="nsx-4", nested=False),
                ProfileItemView(
                    component_uid="ubuntu-24",
                    nested=True,
                    network=ComponentNetworkSpec(
                        ip="192.168.50.10/24", portgroup="VM Network"
                    ),
                ),
            ]
        },
    )()
    lines = profile_item_output(profile).splitlines()
    assert "Host Id: 71, VLAN: 64" in lines[0]
    assert "(Nested)" in lines[1]
    assert "(Not nested)" in lines[2]
    assert "ip: 192.168.50.10/24, portgroup: VM Network" in lines[3]
