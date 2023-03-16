from datetime import datetime

from sqlmodel import SQLModel

from zpodapi.lib.schema_base import Empty, Field, Opt, Req
from zpodapi.permission_groups.permission_group_schemas import PermissionGroupView
from zpodapi.users.user_schemas import UserView

from .instance_component__schemas import InstanceComponentView
from .instance_feature__schemas import InstanceFeatureView
from .instance_network__schemas import InstanceNetworkView

example_creation_date = datetime(2023, 1, 1)


# TODO: Remove when real version is ready
class EndpointView(SQLModel):
    id: int = Req(example=1)


class InstancePermissionView(SQLModel):
    id: int = Req(example=1)
    name: str = Req(example="owner")
    permission: str = Req(example="zpodadmin")
    users: list[UserView] = []
    groups: list["PermissionGroupView"] = []


class InstanceCreate(SQLModel, extra="forbid"):
    name: str = Req(example="tanzu-lab")
    description: str = Empty(example="Tanzu Lab zPod")
    domain: str = Req(example="tanzu-lab.maindomain.com")
    endpoint_id: int = Req(example=1)
    profile: str = Req(example="sddc-profile")


class InstanceUpdate(SQLModel, extra="forbid"):
    id: int = Field(None, example=1)
    description: str = Opt(example="Tanzu Lab zPod")


class InstanceView(SQLModel):
    id: int = Req(example=1)
    name: str = Req(example="tanzu-lab")
    description: str = Req(example="Tanzu Lab zPod")
    domain: str = Req(example="tanzu-lab.maindomain.com")
    profile: str = Req(example="sddc-profile")
    creation_date: datetime = Req(example=example_creation_date)
    last_modified_date: datetime = Req(example=example_creation_date)
    endpoint: "EndpointView"
    networks: list["InstanceNetworkView"] = []
    components: list["InstanceComponentView"] = []
    permissions: list["InstancePermissionView"] = []
    features: list["InstanceFeatureView"] = []
