from datetime import datetime
from ipaddress import IPv4Network

from sqlmodel import SQLModel

from zpodapi.lib.schema_base import Opt, Req
from zpodapi.permission_groups.permission_group_schemas import PermissionGroupView
from zpodapi.users.user_schemas import UserView

example_creation_date = datetime(2023, 1, 1)


# class InstanceCreate(SQLModel, extra="forbid"):
#     username: str = Req(example="jdoe")
#     email: EmailStr = Req(example="jdoe@example.com")
#     description: str = Req(example="Sample User")
#     ssh_key: str = Field("")
#     superadmin: bool = False


# class InstanceUpdate(SQLModel, extra="forbid"):
#     id: int = Field(None, example=1)
#     description: str | None = Field(None, example="Sample User")
#     ssh_key: str | None = Field(None)
#     superadmin: bool | None = Field(None, example=False)


class EndpointView(SQLModel):
    id: int = Req(example=1)


class InstanceComponentView(SQLModel):
    id: int = Req(example=1)
    component_uid: str = Req(example="vcd-10.2")


class InstanceNetworkView(SQLModel):
    id: int = Req(example=1)
    cidr: IPv4Network = Req(example=1)


class InstancePermissionView(SQLModel):
    id: int = Req(example=1)
    name: str = Req(example="owner")
    permission: str = Req(example="zpodadmin")
    users: list[UserView] = []
    groups: list[PermissionGroupView] = []


class InstanceView(SQLModel):
    id: int = Req(example=1)
    name: str = Req(example="tanzu-lab")
    description: str = Req(example="Tanzu Lab zPod")
    password: str = Req(example="amazingpassword")
    domain: str = Req(example="tanzu-lab.maindomain.com")
    creation_date: datetime = Req(example=example_creation_date)
    last_modified_date: datetime = Req(example=example_creation_date)
    endpoint: EndpointView
    networks: list[InstanceNetworkView] = []
    components: list[InstanceComponentView] = []
    permissions: list[InstancePermissionView] = []
