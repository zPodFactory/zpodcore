from datetime import datetime
from typing import Any

from pydantic import StringConstraints
from typing_extensions import Annotated

from zpodapi.lib.schema_base import Field, SchemaBase
from zpodcommon import enums

from ..endpoints.endpoint__schemas import EndpointView
from .zpod_component__schemas import ZpodComponentView
from .zpod_network__schemas import ZpodNetworkView
from .zpod_permission__schemas import ZpodPermissionView

example_creation_date = datetime(2023, 1, 1)


class D:
    id = {"example": 1}
    name = {"example": "demo"}
    description = {"example": "Demo zPod"}
    password = {"example": "yZnqji!a4xbo"}
    domain = {"example": "demo.maindomain.com"}
    endpoint_id = {"example": 1}
    profile = {"example": "sddc"}
    enet_name = {"example": "advanced_networking"}
    status = {"example": enums.ZpodStatus.ACTIVE}
    creation_date = {"example": datetime(2023, 1, 1)}
    last_modified_date = {"example": datetime(2023, 1, 1)}
    features = {"example": {'featureOne': {'option': 'example'}, 'featureTwo': {'property': 'sample'}}}

class ZpodCreate(SchemaBase):
    name: Annotated[str, StringConstraints(to_lower=True)] = Field(..., D.name)
    description: str = Field("", D.description)
    domain: str = Field("", D.domain)
    endpoint_id: int = Field(..., D.endpoint_id)
    profile: str = Field(..., D.profile)
    enet_name: str | None = Field(None, D.enet_name)
    features: dict[str, Any] | None = Field(None, D.features)


class ZpodUpdate(SchemaBase):
    description: str | None = Field(None, D.description)
    features: dict[str, Any] | None = Field(None, D.features)


class ZpodView(SchemaBase):
    id: int = Field(..., D.id)
    name: str = Field(..., D.name)
    description: str = Field(..., D.description)
    password: str = Field(..., D.password)
    domain: str = Field(..., D.domain)
    profile: str = Field(..., D.profile)
    status: enums.ZpodStatus = Field(..., D.status)
    creation_date: datetime = Field(..., D.creation_date)
    last_modified_date: datetime = Field(..., D.last_modified_date)
    features: dict[str, Any] | None = Field(None, D.features)
    endpoint: EndpointView
    networks: list["ZpodNetworkView"] = []
    components: list["ZpodComponentView"] = []
    permissions: list["ZpodPermissionView"] = []
