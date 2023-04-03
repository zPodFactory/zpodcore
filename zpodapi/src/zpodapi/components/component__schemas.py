from zpodapi.lib.schema_base import Field, SchemaBase


class D:
    id = {"example": 1}
    component_uid = {"example": "vcda-4.4.1"}
    component_name = {"example": "vcda"}
    component_version = {"example": "4.4.1"}
    component_description = {"example": "VMWare NSX"}
    library_name = {"example": "main"}
    filename = {"example": "vmware_nsx/vmware-nsxt-4.0.1.1.json"}
    enabled = {"example": False}
    status = {"example": "SCHEDULED"}


class ComponentView(SchemaBase):
    id: str = Field(..., D.id)
    component_uid: str = Field(..., D.component_uid)
    component_name: str = Field(..., D.component_name)
    component_version: str = Field(..., D.component_version)
    component_description: str = Field(..., D.component_description)


class ComponentViewFull(ComponentView):
    library_name: str = Field(..., D.library_name)
    filename: str = Field(..., D.filename)
    enabled: bool = Field(..., D.enabled)
    status: str = Field(..., D.status)
