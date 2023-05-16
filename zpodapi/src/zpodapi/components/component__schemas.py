from zpodcommon.enums import ComponentStatus, ComponentDownloadStatus
from zpodapi.lib.schema_base import Field, SchemaBase


class D:
    id = {"example": 1}
    component_uid = {"example": "vcda-4.4.1"}
    component_name = {"example": "vcda"}
    component_version = {"example": "4.4.1"}
    component_description = {"example": "VMware Cloud Director Availabilty"}
    library_name = {"example": "main"}
    filename = {
        "example": "VMware-Cloud-Director-Availability-Provider-4.4.1.4448762-b80bae6591_OVF10.ova"
    }
    jsonfile = {
        "example": "/library/default/vmware/vmware_cloud_director_availability/4.4.1.json"
    }
    status = {"example": ComponentStatus.ACTIVE}
    download_status = {"example": ComponentDownloadStatus.SCHEDULED}


class ComponentView(SchemaBase):
    id: str = Field(..., D.id)
    component_uid: str = Field(..., D.component_uid)
    component_name: str = Field(..., D.component_name)
    component_version: str = Field(..., D.component_version)
    component_description: str = Field(..., D.component_description)


class ComponentViewFull(ComponentView):
    library_name: str = Field(..., D.library_name)
    filename: str = Field(..., D.filename)
    jsonfile: str = Field(..., D.jsonfile)
    status: str = Field(..., D.status)
    download_status: str = Field(..., D.download_status)
