from zpodapi.components.component__schemas import ComponentView
from zpodapi.lib.schema_base import Field, SchemaBase


class D:
    id = {"example": 1}
    component_uid = {"example": "esxi-8.0u3e"}
    host_id = {"example": 13}
    ip = {"example": "10.196.176.13"}
    hostname = {"example": "esxi13"}
    fqdn = {"example": "esxi13.demo.zpodfactory.io"}
    password = {"example": "yZnqji!a4xbo"}
    usernames = {
        "example": [
            {"username": "administrator@demo.zpodfactory.io", "type": "ui"},
            {"username": "root", "type": "ssh"},
        ]
    }
    vcpu = {"example": 4}
    vmem = {"example": 16}
    vnics = {"example": 4}
    vdisks = {"example": [10, 400]}
    nested = {
        "example": True,
        "description": "Deploy nested in the zPod (true) or on the endpoint "
        "(false). Default: the component's component_isnested.",
    }
    network = {
        "description": "Nested components only: the network to deploy with. "
        "Every field is optional; left out, the zPod's defaults apply.",
    }
    vlan_id = {
        "example": 64,
        "description": "Put the component on the zPod network with this VLAN, its "
        "interface tagged (ESXi). host_id is the last octet in that network's /24.",
    }
    status = {"example": "ACTIVE"}


class ComponentNetworkSpec(SchemaBase):
    ip: str | None = Field(
        None,
        {
            "example": "10.42.111.20/24",
            "description": "Address with its prefix, for a subnet the portgroup's "
            "VLAN can't give (an isolated lab). Default: host_id on the network "
            "the portgroup carries.",
        },
    )
    gateway: str | None = Field(
        None,
        {
            "example": "10.42.111.1",
            "description": "Default: the gateway of the zPod network holding the IP.",
        },
    )
    dns: str | None = Field(
        None, {"example": "10.42.111.1", "description": "Default: zcore."}
    )
    portgroup: str | None = Field(
        None,
        {
            "example": "VM Network",
            "description": "An existing portgroup of the zPod's vCenter, by name "
            "or inventory path; every NIC goes on it. Its VLAN picks the zPod "
            "network the address comes from. Default: VM Network.",
        },
    )


class ZpodComponentView(SchemaBase):
    component: ComponentView
    ip: str | None = Field(None, D.ip)
    hostname: str | None = Field(None, D.hostname)
    fqdn: str | None = Field(None, D.fqdn)
    password: str | None = Field(None, D.password)
    usernames: list[dict[str, str | None]] | None = Field(None, D.usernames)
    vcpu: int | None = Field(None, D.vcpu)
    vmem: int | None = Field(None, D.vmem)
    vnics: int | None = Field(None, D.vnics)
    vdisks: list[int] | None = Field(None, D.vdisks)
    status: str = Field(None, D.status)


class ZpodComponentCreate(SchemaBase):
    component_uid: str = Field(..., D.component_uid)
    host_id: int | None = Field(None, D.host_id)
    hostname: str | None = Field(None, D.hostname)
    vcpu: int | None = Field(None, D.vcpu)
    vmem: int | None = Field(None, D.vmem)
    vnics: int | None = Field(None, D.vnics)
    vdisks: list[int] | None = Field(None, D.vdisks)
    nested: bool | None = Field(None, D.nested)
    network: ComponentNetworkSpec | None = Field(None, D.network)
    vlan_id: int | None = Field(None, D.vlan_id)
