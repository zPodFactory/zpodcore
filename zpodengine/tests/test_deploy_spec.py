"""component_deploy_extra_config: guestinfo.* keys rendered from the library JSON."""

import base64
import gzip
import json

import pytest
import yaml

from zpodengine.lib.deploy_spec import (
    ExtraConfigError,
    render_deploy_spec,
    render_extra_config,
)

VARS = {
    "zpod_hostname": "node1",
    "zpod_domain": "lab.zpod.example",
    "zpod_ipaddress": "10.42.111.30",
    "zpod_netprefix": 24,
    "zpod_netmask": "255.255.255.0",
    "zpod_gateway": "10.42.111.1",
    "zpod_dns": "10.42.111.2",
    "zpod_ntp": "10.42.111.1",
    "zpod_password": "it's: a #secret!",
    "zpod_sshkey": "ssh-ed25519 AAAAC3Nza zpodfactory",
}


def b64decode(value: str) -> str:
    return base64.b64decode(value).decode()


def test_deploy_spec_b64encode_filter():
    spec = {
        "PropertyMapping": [
            {
                "Key": "k",
                "Value": "{% filter b64encode %}{{zpod_hostname}}{% endfilter %}",
            }
        ]
    }
    assert render_deploy_spec(spec, **VARS)["PropertyMapping"][0]["Value"] == "bm9kZTE="


def test_no_extra_config_is_nothing_to_set():
    assert render_extra_config(None, **VARS) == {}
    assert render_extra_config({}, **VARS) == {}


def test_string_values_are_rendered_as_is():
    out = render_extra_config(
        {
            "guestinfo.afterburn.initrd.network-kargs": "ip={{zpod_ipaddress}}::{{zpod_gateway}}:{{zpod_netmask}}:{{zpod_hostname}}:ens192:none:{{zpod_dns}}"
        },
        **VARS,
    )
    assert out == {
        "guestinfo.afterburn.initrd.network-kargs": "ip=10.42.111.30::10.42.111.1:255.255.255.0:node1:ens192:none:10.42.111.2"
    }


def test_talos_metadata_yaml():
    out = render_extra_config(
        {
            "guestinfo.metadata": {
                "format": "yaml",
                "content": {
                    "instance-id": "{{zpod_hostname}}",
                    "local-hostname": "{{zpod_hostname}}.{{zpod_domain}}",
                    "network": {
                        "version": 2,
                        "ethernets": {
                            "eth0": {
                                "addresses": ["{{zpod_ipaddress}}/{{zpod_netprefix}}"],
                                "gateway4": "{{zpod_gateway}}",
                                "nameservers": {"addresses": ["{{zpod_dns}}"]},
                            }
                        },
                    },
                },
            }
        },
        **VARS,
    )
    assert out["guestinfo.metadata.encoding"] == "base64"
    assert yaml.safe_load(b64decode(out["guestinfo.metadata"])) == {
        "instance-id": "node1",
        "local-hostname": "node1.lab.zpod.example",
        "network": {
            "version": 2,
            "ethernets": {
                "eth0": {
                    "addresses": ["10.42.111.30/24"],
                    "gateway4": "10.42.111.1",
                    "nameservers": {"addresses": ["10.42.111.2"]},
                }
            },
        },
    }


def test_cloud_config_keeps_awkward_strings_intact():
    out = render_extra_config(
        {
            "guestinfo.userdata": {
                "format": "cloud-config",
                "content": {
                    "chpasswd": {
                        "expire": False,
                        "users": [
                            {
                                "name": "root",
                                "password": "{{zpod_password}}",
                                "type": "text",
                            }
                        ],
                    },
                    "ssh_authorized_keys": ["{{zpod_sshkey}}"],
                },
            }
        },
        **VARS,
    )
    text = b64decode(out["guestinfo.userdata"])
    assert text.startswith("#cloud-config\n")
    doc = yaml.safe_load(text)
    assert doc["chpasswd"]["users"][0]["password"] == "it's: a #secret!"
    assert doc["chpasswd"]["expire"] is False
    assert doc["ssh_authorized_keys"] == ["ssh-ed25519 AAAAC3Nza zpodfactory"]


def test_ignition_json_with_lines_helper():
    out = render_extra_config(
        {
            "guestinfo.ignition.config.data": {
                "format": "json",
                "content": {
                    "ignition": {"version": "3.3.0"},
                    "storage": {
                        "files": [
                            {
                                "path": "/etc/systemd/network/00-zpod.network",
                                "mode": 420,
                                "contents": {
                                    "lines": [
                                        "[Network]",
                                        "Address={{zpod_ipaddress}}/{{zpod_netprefix}}",
                                    ]
                                },
                            }
                        ]
                    },
                },
            }
        },
        **VARS,
    )
    assert out["guestinfo.ignition.config.data.encoding"] == "base64"
    ign = json.loads(b64decode(out["guestinfo.ignition.config.data"]))
    f = ign["storage"]["files"][0]
    assert f["mode"] == 420
    prefix, data = f["contents"]["source"].split(",", 1)
    assert prefix == "data:;base64"
    assert b64decode(data) == "[Network]\nAddress=10.42.111.30/24\n"


def test_gzip_and_none_encodings():
    out = render_extra_config(
        {
            "guestinfo.metadata": {
                "format": "json",
                "encoding": "gzip+base64",
                "content": {"a": "{{zpod_hostname}}"},
            },
            "guestinfo.raw": {
                "format": "json",
                "encoding": "none",
                "content": {"b": 1},
            },
        },
        **VARS,
    )
    assert (
        gzip.decompress(base64.b64decode(out["guestinfo.metadata"])) == b'{"a":"node1"}'
    )
    assert out["guestinfo.metadata.encoding"] == "gzip+base64"
    assert out["guestinfo.raw"] == '{"b":1}'
    assert "guestinfo.raw.encoding" not in out


def test_an_explicit_matching_encoding_key_is_fine():
    out = render_extra_config(
        {
            "guestinfo.metadata": {"format": "json", "content": {}},
            "guestinfo.metadata.encoding": "base64",
        },
        **VARS,
    )
    assert out["guestinfo.metadata.encoding"] == "base64"


@pytest.mark.parametrize(
    "extra_config, message",
    [
        ({"disk.EnableUUID": "TRUE"}, "only guestinfo.* keys"),
        ({"guestinfo.": "x"}, "only guestinfo.* keys"),
        ({"guestinfo.x": 1}, "a string or an object"),
        ({"guestinfo.x": {"format": "toml", "content": {}}}, "format must be one of"),
        (
            {"guestinfo.x": {"format": "json", "encoding": "rot13", "content": {}}},
            "encoding must be one of",
        ),
        ({"guestinfo.x": {"format": "json"}}, "needs a content"),
        (
            {"guestinfo.x": {"format": "json", "content": {}, "extra": 1}},
            "unknown field(s) extra",
        ),
        ({"guestinfo.x": "{{zpod_typo}}"}, "zpod_typo"),
        (
            {"guestinfo.x": {"format": "json", "content": {"k": "{{ unclosed"}}},
            "guestinfo.x",
        ),
        (
            {
                "guestinfo.x": {"format": "json", "content": {}},
                "guestinfo.x.encoding": "none",
            },
            "base64-encoded",
        ),
        (["guestinfo.x"], "must be an object"),
    ],
)
def test_invalid_extra_config_is_refused(extra_config, message):
    with pytest.raises(ExtraConfigError) as e:
        render_extra_config(extra_config, **VARS)
    assert message in str(e.value)
