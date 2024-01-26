from datetime import datetime
from typing import List

from pydantic import StringConstraints
from typing_extensions import Annotated

from zpodapi.lib.schema_base import Field, SchemaBase

example_creation_date = datetime(2023, 1, 1)


class D:
    id = {"example": 1}
    name = {"example": "sddc", "regex": r"^[A-Za-z0-9_-]+$"}
    creation_date = {"example": example_creation_date}
    last_modified_date = {"example": example_creation_date}

    class profile:
        component_uid = {"example": "zbox-11.7"}
        host_id = {"example": 11}
        hostname = {"example": "zbox"}
        vcpu = {"example": 4}
        vmem = {"example": 12}
        vdisk = {"example": [40, 800]}


class ProfileItemView(SchemaBase):
    component_uid: str = Field(..., D.profile.component_uid)
    host_id: int | None = Field(None, D.profile.host_id)
    hostname: str | None = Field(None, D.profile.hostname)
    vcpu: int | None = Field(None, D.profile.vcpu)
    vmem: int | None = Field(None, D.profile.vmem)
    vdisks: list[int] | None = Field(None, D.profile.vdisk)


class ProfileView(SchemaBase):
    id: int = Field(..., D.id)
    name: str = Field(..., D.name)
    profile: List[ProfileItemView | List[ProfileItemView]]
    creation_date: datetime = Field(..., D.creation_date)
    last_modified_date: datetime = Field(..., D.last_modified_date)


class ProfileItemCreate(SchemaBase):
    component_uid: str = Field(..., D.profile.component_uid)
    host_id: int | None = Field(None, D.profile.host_id)
    hostname: str | None = Field(None, D.profile.hostname)
    vcpu: int | None = Field(None, D.profile.vcpu)
    vmem: int | None = Field(None, D.profile.vmem)
    vdisks: list[int] | None = Field(None, D.profile.vdisk)


class ProfileCreate(SchemaBase):
    name: Annotated[str, StringConstraints(to_lower=True)] = Field(..., D.name)
    profile: List[ProfileItemCreate | List[ProfileItemCreate]]


class ProfileItemUpdate(SchemaBase):
    component_uid: str = Field(..., D.profile.component_uid)
    host_id: int | None = Field(None, D.profile.host_id)
    hostname: str | None = Field(None, D.profile.hostname)
    vcpu: int | None = Field(None, D.profile.vcpu)
    vmem: int | None = Field(None, D.profile.vmem)
    vdisks: list[int] | None = Field(None, D.profile.vdisk)


class ProfileUpdate(SchemaBase):
    name: Annotated[str, StringConstraints(to_lower=True)] | None = Field(None, D.name)
    profile: List[ProfileItemUpdate | List[ProfileItemUpdate]] | None = None
