from zpodapi.components.component__schemas import ComponentView
from zpodapi.lib.schema_base import Field, SchemaBase


class D:
    id = {"example": 1}
    component_uid = {"example": "vcda-4.4.1"}
    data = {"example": "{}"}
    extra_id = {"example": "11"}

    class data:
        mgmt_ip = {"example": 11}


class InstanceComponentDataView(SchemaBase):
    mgmt_ip: int | None = Field(None, D.data.mgmt_ip)


class InstanceComponentView(SchemaBase):
    component: ComponentView
    data: InstanceComponentDataView


class InstanceComponentDataCreate(SchemaBase):
    mgmt_ip: int = Field(None, D.data.mgmt_ip)


class InstanceComponentCreate(SchemaBase):
    component_uid: str = Field(..., D.component_uid)
    extra_id: str = Field("", D.extra_id)
    data: InstanceComponentDataCreate
