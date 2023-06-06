from datetime import datetime

from pydantic import constr

from zpodapi.lib.schema_base import Field, SchemaBase
from zpodcommon import enums

from ..endpoints.endpoint__schemas import EndpointView
from .instance_component__schemas import InstanceComponentView
from .instance_feature__schemas import InstanceFeatureView
from .instance_network__schemas import InstanceNetworkView
from .instance_permission__schemas import InstancePermissionView

example_creation_date = datetime(2023, 1, 1)


class D:
    id = {"example": 1}
    name = {"example": "demo"}
    description = {"example": "Demo zPod"}
    password = {"example": "yZnqji!a4xbo"}
    domain = {"example": "demo.maindomain.com"}
    endpoint_id = {"example": 1}
    profile = {"example": "sddc"}
    enet_project_id = {"example": "advanced_networking"}
    status = {"example": enums.InstanceStatus.ACTIVE}
    creation_date = {"example": datetime(2023, 1, 1)}
    last_modified_date = {"example": datetime(2023, 1, 1)}


class InstanceCreate(SchemaBase):
    name: constr(to_lower=True) = Field(..., D.name)
    description: str = Field("", D.description)
    domain: str = Field("", D.domain)
    endpoint_id: int = Field(..., D.endpoint_id)
    profile: str = Field(..., D.profile)
    enet_project_id: str = Field(None, D.enet_project_id)


class InstanceUpdate(SchemaBase):
    description: str | None = Field(None, D.description)


class InstanceView(SchemaBase):
    id: int = Field(..., D.id)
    name: str = Field(..., D.name)
    description: str = Field(..., D.description)
    password: str = Field(..., D.password)
    domain: str = Field(..., D.domain)
    profile: str = Field(..., D.profile)
    status: enums.InstanceStatus = Field(..., D.status)
    creation_date: datetime = Field(..., D.creation_date)
    last_modified_date: datetime = Field(..., D.last_modified_date)
    endpoint: EndpointView
    networks: list["InstanceNetworkView"] = []
    components: list["InstanceComponentView"] = []
    permissions: list["InstancePermissionView"] = []
    features: list["InstanceFeatureView"] = []
