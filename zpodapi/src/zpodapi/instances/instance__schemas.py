from datetime import datetime

from sqlmodel import SQLModel

from zpodapi.lib.schema_base import Empty, Opt, Req

from ..endpoints.endpoint_schemas import EndpointView
from ..permission_groups.permission_group_schemas import PermissionGroupView
from ..users.user_schemas import UserView
from .instance__enums import InstanceStatusEnum
from .instance_component__schemas import InstanceComponentView
from .instance_feature__schemas import InstanceFeatureView
from .instance_network__schemas import InstanceNetworkView

example_creation_date = datetime(2023, 1, 1)


class InstancePermissionView(SQLModel):
    id: int = Req(example=1)
    permission: str = Req(example="zpodowner")
    users: list[UserView] = []
    groups: list["PermissionGroupView"] = []


class InstanceCreate(SQLModel, extra="forbid"):
    name: str = Req(example="tanzu-lab")
    description: str = Empty(example="Tanzu Lab zPod")
    domain: str = Req(example="tanzu-lab.maindomain.com")
    endpoint_id: int = Req(example=1)
    profile: str = Req(example="sddc-profile")


class InstanceUpdate(SQLModel):
    id: int = Opt()
    description: str = Opt()

    class Config:
        extra = "forbid"
        schema_extra = dict(
            example=dict(
                description="Tanzu Lab zPod",
            )
        )


class InstanceDelete(SQLModel):
    status: InstanceStatusEnum = Req()


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
    status: InstanceStatusEnum = Req(example=InstanceStatusEnum.ACTIVE)
