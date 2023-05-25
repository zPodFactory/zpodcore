from zpodapi.components.component__schemas import ComponentView
from zpodapi.lib.schema_base import Field, SchemaBase


class D:
    id = {"example": 1}
    component_uid = {"example": "vcda-4.4.1"}

    class data:
        last_octet = {"example": 11}
        vcpu = {"example": 4}
        vmem = {"example": 16}


class InstanceComponentDataView(SchemaBase):
    last_octet: int | None = Field(None, D.data.last_octet)
    vcpu: int | None = Field(None, D.data.vcpu)
    vmem: int | None = Field(None, D.data.vmem)


class InstanceComponentView(SchemaBase):
    component: ComponentView
    data: InstanceComponentDataView


class InstanceComponentDataCreate(SchemaBase):
    last_octet: int = Field(None, D.data.last_octet)
    vcpu: int = Field(None, D.data.vcpu)
    vmem: int = Field(None, D.data.vmem)


class InstanceComponentCreate(SchemaBase):
    component_uid: str = Field(..., D.component_uid)
    data: InstanceComponentDataCreate
