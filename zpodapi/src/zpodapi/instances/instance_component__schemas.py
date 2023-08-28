from zpodapi.components.component__schemas import ComponentView
from zpodapi.lib.schema_base import Field, SchemaBase


class D:
    id = {"example": 1}
    component_uid = {"example": "esxi-8.0u1a"}
    host_id = {"example": 13}
    ip = {"example": "10.196.176.13"}
    hostname = {"example": "esxi13"}
    fqdn = {"example": "esxi13.demo.zpodfactory.io"}
    vcpu = {"example": 4}
    vmem = {"example": 16}


class InstanceComponentView(SchemaBase):
    component: ComponentView
    ip: str | None = Field(None, D.ip)
    hostname: str | None = Field(None, D.hostname)
    fqdn: str | None = Field(None, D.fqdn)
    vcpu: int | None = Field(None, D.vcpu)
    vmem: int | None = Field(None, D.vmem)


class InstanceComponentCreate(SchemaBase):
    component_uid: str = Field(..., D.component_uid)
    host_id: int | None = Field(None, D.host_id)
    hostname: str | None = Field(None, D.hostname)
    vcpu: int | None = Field(None, D.vcpu)
    vmem: int | None = Field(None, D.vmem)
