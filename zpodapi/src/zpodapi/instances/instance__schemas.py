from datetime import datetime

from zpodapi.lib.schema_base import Field, SchemaBase
from zpodcommon import enums

from .instance_component__schemas import InstanceComponentView
from .instance_feature__schemas import InstanceFeatureView
from .instance_network__schemas import InstanceNetworkView
from .instance_permission__schemas import InstancePermissionView

example_creation_date = datetime(2023, 1, 1)


class D:
    id = {"example": 1}
    name = {"example": "tanzu-lab"}
    description = {"example": "Tanzu Lab zPod"}
    domain = {"example": "tanzu-lab.maindomain.com"}
    endpoint_id = {"example": 1}
    profile = {"example": "sddc"}
    status = {"example": enums.InstanceStatus.ACTIVE}
    creation_date = {"example": datetime(2023, 1, 1)}
    last_modified_date = {"example": datetime(2023, 1, 1)}
    endpoint_id = {"example": 1}


class InstanceCreate(SchemaBase):
    name: str = Field(..., D.name)
    description: str = Field("", D.description)
    domain: str = Field(..., D.domain)
    endpoint_id: int = Field(..., D.endpoint_id)
    profile: str = Field(..., D.profile)


class InstanceUpdate(SchemaBase):
    description: str | None = Field(None, D.description)


class InstanceView(SchemaBase):
    id: int = Field(..., D.id)
    name: str = Field(..., D.name)
    description: str = Field(..., D.description)
    domain: str = Field(..., D.domain)
    profile: str = Field(..., D.profile)
    status: enums.InstanceStatus = Field(..., D.status)
    creation_date: datetime = Field(..., D.creation_date)
    last_modified_date: datetime = Field(..., D.last_modified_date)
    endpoint_id: int = Field(..., D.endpoint_id)
    networks: list["InstanceNetworkView"] = []
    components: list["InstanceComponentView"] = []
    permissions: list["InstancePermissionView"] = []
    features: list["InstanceFeatureView"] = []
