from ipaddress import IPv4Network
from typing import TYPE_CHECKING, Any, Dict, List

from sqlmodel import JSON, Column, Field, Relationship

from zpodcommon.models.model_base import ModelBase

from .mixins import CommonDatesMixin

if TYPE_CHECKING:
    from .component_models import Component
    from .endpoint_models import Endpoint
    from .permission_group_models import PermissionGroup
    from .user_models import User


class Zpod(CommonDatesMixin, ModelBase, table=True):
    __tablename__ = "zpods"

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
    )
    name: str = Field(
        default=...,
        index=True,
        nullable=False,
    )
    description: str = Field(
        default="",
        nullable=False,
    )
    password: str = Field(
        default="",
        nullable=False,
    )
    domain: str = Field(
        default="",
        nullable=False,
    )
    profile: str = Field(
        default="",
        nullable=False,
    )
    endpoint_id: int = Field(
        default=...,
        nullable=False,
        foreign_key="endpoints.id",
    )
    status: str = Field(
        default=...,
        nullable=False,
    )
    features: Dict[str, Any] = Field(
        default={},
        sa_column=Column(JSON, nullable=False, index=False),
    )

    components: List["ZpodComponent"] = Relationship(
        back_populates="zpod",
        sa_relationship_kwargs={
            "cascade": "all,delete,delete-orphan",
        },
    )
    networks: List["ZpodNetwork"] = Relationship(
        back_populates="zpod",
        sa_relationship_kwargs={
            "cascade": "all,delete,delete-orphan",
        },
    )
    permissions: List["ZpodPermission"] = Relationship(
        back_populates="zpod",
        sa_relationship_kwargs={
            "cascade": "all,delete,delete-orphan",
        },
    )
    endpoint: "Endpoint" = Relationship()


class ZpodComponent(CommonDatesMixin, ModelBase, table=True):
    __tablename__ = "zpod_components"

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
    )
    zpod_id: int = Field(
        default=...,
        nullable=False,
        foreign_key="zpods.id",
    )
    component_id: int = Field(
        default=...,
        nullable=False,
        foreign_key="components.id",
    )
    status: str = Field(
        default=...,
        nullable=False,
    )
    ip: str = Field(
        default=...,
        nullable=True,
    )
    hostname: str = Field(
        default=...,
        nullable=True,
    )
    fqdn: str = Field(
        default=...,
        nullable=True,
    )

    @property
    def password(self) -> str | None:
        return self.zpod.password if self.zpod else None

    @property
    def usernames(self) -> list[dict[str, str]] | None:
        if not self.zpod or not self.component:
            return None
        return self.component.get_usernames(
            zpod_domain=self.zpod.domain,
        )

    zpod: "Zpod" = Relationship(back_populates="components")
    component: "Component" = Relationship()

class ZpodNetwork(ModelBase, table=True):
    __tablename__ = "zpod_networks"

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
    )
    zpod_id: int = Field(
        default=...,
        nullable=False,
        foreign_key="zpods.id",
    )
    cidr: IPv4Network = Field(
        default=...,
        nullable=False,
    )

    zpod: "Zpod" = Relationship(back_populates="networks")


class ZpodPermission(ModelBase, table=True):
    __tablename__ = "zpod_permissions"

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
    )
    zpod_id: int = Field(
        default=...,
        nullable=False,
        foreign_key="zpods.id",
    )
    permission: str = Field(
        default=...,
        nullable=False,
    )

    zpod: "Zpod" = Relationship(back_populates="permissions")
    users: List["User"] = Relationship(
        back_populates="zpod_permissions",
        sa_relationship_kwargs={
            "secondary": "zpod_permission_user_link",
        },
    )
    permission_groups: List["PermissionGroup"] = Relationship(
        back_populates="zpod_permissions",
        sa_relationship_kwargs={
            "secondary": "zpod_permission_group_link",
        },
    )


class ZpodPermissionUserLink(ModelBase, table=True):
    __tablename__ = "zpod_permission_user_link"

    zpod_permission_id: int = Field(
        default=...,
        primary_key=True,
        nullable=False,
        foreign_key="zpod_permissions.id",
    )
    user_id: int = Field(
        default=...,
        primary_key=True,
        nullable=False,
        foreign_key="users.id",
    )


class ZpodPermissionGroupLink(ModelBase, table=True):
    __tablename__ = "zpod_permission_group_link"

    zpod_permission_id: int = Field(
        default=...,
        primary_key=True,
        nullable=False,
        foreign_key="zpod_permissions.id",
    )
    permission_group_id: int = Field(
        default=...,
        primary_key=True,
        nullable=False,
        foreign_key="permission_groups.id",
    )
