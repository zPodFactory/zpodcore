from datetime import datetime
from typing import TYPE_CHECKING, List

from pydantic import EmailStr
from sqlmodel import AutoString, Field, Relationship

from zpodcommon.models.model_base import ModelBase

if TYPE_CHECKING:
    from .endpoint_models import EndpointPermission
    from .permission_group_models import PermissionGroup
    from .zpod_models import ZpodPermission

from .mixins import CommonDatesMixin


class User(CommonDatesMixin, ModelBase, table=True):
    __tablename__ = "users"

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
    )
    username: str = Field(
        default=...,
        unique=True,
        index=True,
        nullable=False,
    )
    email: EmailStr = Field(
        default=...,
        unique=True,
        index=True,
        nullable=False,
        sa_type=AutoString,
    )
    description: str = Field(
        default="",
        nullable=False,
    )
    api_token: str = Field(
        default="",
        index=True,
        nullable=False,
    )
    ssh_key: str = Field(
        default="",
        nullable=False,
    )
    creation_date: datetime = Field(
        sa_column_kwargs={"default": datetime.utcnow},
        nullable=False,
    )
    last_connection_date: datetime = Field(
        default=None,
        nullable=True,
    )
    superadmin: bool = Field(
        default=False,
        nullable=False,
    )
    status: str = Field(
        default=...,
        nullable=False,
    )

    zpod_permissions: List["ZpodPermission"] = Relationship(
        back_populates="users",
        sa_relationship_kwargs={
            "secondary": "zpod_permission_user_link",
        },
    )
    endpoint_permissions: List["EndpointPermission"] = Relationship(
        back_populates="users",
        sa_relationship_kwargs={
            "secondary": "endpoint_permission_user_link",
        },
    )
    permission_groups: List["PermissionGroup"] = Relationship(
        back_populates="users",
        sa_relationship_kwargs={
            "secondary": "permission_group_user_link",
        },
    )
