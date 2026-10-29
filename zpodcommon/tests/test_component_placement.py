from zpodcommon.lib.component_placement import (
    component_isnested,
    nested_override_error,
)


def test_component_isnested_defaults_to_the_library_json():
    assert component_isnested({"component_isnested": True}, None) is True
    assert component_isnested({"component_isnested": False}, None) is False
    assert component_isnested({}, None) is False
    assert component_isnested(None, None) is False


def test_component_isnested_override_wins():
    assert component_isnested({"component_isnested": True}, False) is False
    assert component_isnested({"component_isnested": False}, True) is True


def test_nested_override_error():
    assert nested_override_error("vrops", True) is None
    assert nested_override_error("vrops", False) is None
    assert nested_override_error("esxi", None) is None
    # A fixed component accepts its own default, refuses a change.
    esxi, vcsa = {"component_isnested": False}, {"component_isnested": True}
    assert nested_override_error("esxi", False, esxi) is None
    assert nested_override_error("vcsa", True, vcsa) is None
    assert nested_override_error("esxi", True, esxi) == (
        "nested can't be set to true on esxi: its placement is fixed (on the endpoint)"
    )
    assert nested_override_error("vcsa", False, vcsa) == (
        "nested can't be set to false on vcsa: its placement is fixed "
        "(nested in the zPod)"
    )


def test_component_options_error():
    from zpodcommon.lib.component_placement import component_options_error

    nested_json = {
        "component_isnested": True,
        "component_deploy_govc_spec": {"NetworkMapping": [{"Name": "n"}]},
    }
    l1_json = {**nested_json, "component_isnested": False}
    net = {"ip": "10.42.111.20/24", "portgroup": "VM Network"}

    assert component_options_error("vrops", nested_json, network=net) is None
    assert component_options_error("ubuntu", l1_json, nested=True, network=net) is None
    assert "only for nested" in component_options_error("ubuntu", l1_json, network=net)
    assert "only for nested" in component_options_error(
        "vrops", nested_json, nested=False, network=net
    )
    assert "vnics can't be set" in component_options_error(
        "vrops", nested_json, vnics=2
    )
    assert component_options_error("zbox", l1_json, vnics=2) is None
    assert component_options_error("vcsa", nested_json, network=net) == (
        "network can't be set on vcsa: component is protected"
    )
    # Fixed components keep their vnics (esxi uses them).
    assert component_options_error("esxi", l1_json, vnics=4) is None
    no_mapping = {"component_isnested": True, "component_deploy_govc_spec": {}}
    assert "no NetworkMapping" in component_options_error(
        "vrops", no_mapping, network=net
    )
    assert (
        component_options_error("vrops", no_mapping, network={"dns": "1.1.1.1"}) is None
    )
    # A stored profile item's all-null network is no network.
    assert component_options_error("ubuntu", l1_json, network={"ip": None}) is None


def test_vlan_id_options():
    from zpodcommon.lib.component_placement import component_options_error

    esxi = {
        "component_deploy_govc_spec": {
            "PropertyMapping": [{"Key": "guestinfo.vlan", "Value": "{{zpod_vlan}}"}]
        }
    }
    old_esxi = {
        "component_deploy_govc_spec": {
            "PropertyMapping": [{"Key": "guestinfo.vlan", "Value": ""}]
        }
    }
    assert component_options_error("esxi", esxi, vlan_id=64) is None
    assert "doesn't use {{zpod_vlan}}" in component_options_error(
        "esxi", old_esxi, vlan_id=64
    )
    assert "not a VLAN" in component_options_error("esxi", esxi, vlan_id=0)
    assert "vlan_id gives the address" in component_options_error(
        "esxi", esxi, vlan_id=64, network={"ip": "10.96.1.71/26"}
    )


def test_vlan_id_nested_on_a_trunk_portgroup():
    from zpodcommon.lib.component_placement import component_options_error

    spec = {
        "NetworkMapping": [{"Name": "n", "Network": "{{zpod_portgroup}}"}],
        "PropertyMapping": [{"Key": "x.vlan", "Value": "{{zpod_vlan}}"}],
    }
    zbox = {"component_isnested": False, "component_deploy_govc_spec": spec}
    # Nested on a trunk portgroup: allowed, the portgroup is the user's design.
    assert (
        component_options_error(
            "zbox", zbox, vlan_id=64, nested=True, network={"portgroup": "TRUNK"}
        )
        is None
    )
    assert component_options_error("zbox", zbox, vlan_id=64, nested=True) is None
    assert "vlan_id gives the address" in component_options_error(
        "zbox", zbox, vlan_id=64, nested=True, network={"ip": "10.0.0.5/24"}
    )
