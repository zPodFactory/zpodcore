from datetime import datetime
from ipaddress import IPv4Network
from typing import Any

from sqlmodel import SQLModel

from zpodapi.components.component_schemas import ComponentView
from zpodapi.lib.schema_base import Empty, Field, Opt, Req
from zpodapi.permission_groups.permission_group_schemas import PermissionGroupView
from zpodapi.users.user_schemas import UserView

example_creation_date = datetime(2023, 1, 1)


class InstanceCreate(SQLModel, extra="forbid"):
    name: str = Req(example="tanzu-lab")
    description: str = Empty(example="Tanzu Lab zPod")
    domain: str = Req(example="tanzu-lab.maindomain.com")
    endpoint_id: int = Req(example=1)
    profile: str = Req(example="sddc-profile")


class InstanceUpdate(SQLModel, extra="forbid"):
    id: int = Field(None, example=1)
    description: str = Opt(example="Tanzu Lab zPod")


class EndpointView(SQLModel):
    id: int = Req(example=1)


class InstanceComponentView(SQLModel):
    component: ComponentView
    data: dict[Any, Any]


class InstanceNetworkView(SQLModel):
    id: int = Req(example=1)
    cidr: IPv4Network = Req(example=1)


class InstancePermissionView(SQLModel):
    id: int = Req(example=1)
    name: str = Req(example="owner")
    permission: str = Req(example="zpodadmin")
    users: list[UserView] = []
    groups: list[PermissionGroupView] = []


class InstanceFeatureView(SQLModel):
    id: int = Req(example=1)
    data: dict[Any, Any] = Req(example="{'feature':'one'}")


class InstanceView(SQLModel):
    id: int = Req(example=1)
    name: str = Req(example="tanzu-lab")
    description: str = Req(example="Tanzu Lab zPod")
    password: str = Req(example="amazingpassword")
    domain: str = Req(example="tanzu-lab.maindomain.com")
    profile: str = Req(example="sddc-profile")
    creation_date: datetime = Req(example=example_creation_date)
    last_modified_date: datetime = Req(example=example_creation_date)
    endpoint: EndpointView
    networks: list[InstanceNetworkView] = []
    components: list[InstanceComponentView] = []
    permissions: list[InstancePermissionView] = []
    features: list[InstanceFeatureView] = []
