from datetime import datetime
from ipaddress import IPv4Network
from typing import Any, Dict, List

from sqlmodel import JSON, Column, Field, Relationship, SQLModel

from .component_models import Component
from .endpoint_models import Endpoint
from .permission_group_models import PermissionGroup
from .user_models import User


class Instance(SQLModel, table=True):
    __tablename__ = "instances"

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
    )
    name: str = Field(
        default=...,
        unique=True,
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
    creation_date: datetime = Field(
        default=None,
        nullable=False,
    )
    last_modified_date: datetime = Field(
        default=None,
        nullable=False,
    )
    endpoint_id: int = Field(
        default=...,
        nullable=False,
        foreign_key="endpoints.id",
    )

    components: List["InstanceComponent"] = Relationship(
        back_populates="instance",
        sa_relationship_kwargs={
            "cascade": "all,delete,delete-orphan",
        },
    )
    networks: List["InstanceNetwork"] = Relationship(
        back_populates="instance",
        sa_relationship_kwargs={
            "cascade": "all,delete,delete-orphan",
        },
    )
    features: List["InstanceFeature"] = Relationship(
        back_populates="instance",
        sa_relationship_kwargs={
            "cascade": "all,delete,delete-orphan",
        },
    )
    permissions: List["InstancePermission"] = Relationship(
        back_populates="instance",
        sa_relationship_kwargs={
            "cascade": "all,delete,delete-orphan",
        },
    )
    endpoint: "Endpoint" = Relationship()


class InstanceComponent(SQLModel, table=True):
    __tablename__ = "instance_components"

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
    )
    instance_id: int = Field(
        default=...,
        nullable=False,
        foreign_key="instances.id",
    )
    component_uid: str = Field(
        default=...,
        nullable=False,
        foreign_key="components.component_uid",
    )
    data: Dict[Any, Any] | None = Field(
        default={},
        index=False,
        sa_column=Column(JSON),
    )

    instance: "Instance" = Relationship(back_populates="components")
    component: "Component" = Relationship()


class InstanceFeature(SQLModel, table=True):
    __tablename__ = "instance_features"

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
    )
    instance_id: int = Field(
        default=...,
        nullable=False,
        foreign_key="instances.id",
    )
    data: Dict[Any, Any] | None = Field(
        default={},
        index=False,
        sa_column=Column(JSON),
    )

    instance: "Instance" = Relationship(back_populates="features")


class InstanceNetwork(SQLModel, table=True):
    __tablename__ = "instance_networks"

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
    )
    instance_id: int = Field(
        default=...,
        nullable=False,
        foreign_key="instances.id",
    )
    cidr: IPv4Network = Field(
        default=...,
        nullable=False,
    )

    instance: "Instance" = Relationship(back_populates="networks")


class InstancePermissionUserLink(SQLModel, table=True):
    __tablename__ = "instance_permission_user_link"

    instance_permission_id: int = Field(
        default=...,
        primary_key=True,
        nullable=False,
        foreign_key="instance_permissions.id",
    )
    user_id: int = Field(
        default=...,
        primary_key=True,
        nullable=False,
        foreign_key="users.id",
    )
    instance_permission: "InstancePermission" = Relationship(
        back_populates="user_links"
    )
    user: "User" = Relationship()


class InstancePermissionGroupLink(SQLModel, table=True):
    __tablename__ = "instance_permission_group_link"

    instance_permission_id: int = Field(
        default=...,
        primary_key=True,
        nullable=False,
        foreign_key="instance_permissions.id",
    )
    permission_group_id: int = Field(
        default=...,
        primary_key=True,
        nullable=False,
        foreign_key="permission_groups.id",
    )

    instance_permission: "InstancePermission" = Relationship(
        back_populates="group_links"
    )
    permission_group: "PermissionGroup" = Relationship()


class InstancePermission(SQLModel, table=True):
    __tablename__ = "instance_permissions"

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
    )
    instance_id: int = Field(
        default=...,
        nullable=False,
        foreign_key="instances.id",
    )
    name: str = Field(
        default=...,
        nullable=False,
    )
    permission: str = Field(
        default=...,
        nullable=False,
    )

    instance: "Instance" = Relationship(back_populates="permissions")
    user_links: List["InstancePermissionUserLink"] = Relationship(
        back_populates="instance_permission",
        sa_relationship_kwargs={"cascade": "all,delete,delete-orphan"},
    )
    users: List["User"] = Relationship(link_model=InstancePermissionUserLink)

    group_links: List["InstancePermissionGroupLink"] = Relationship(
        back_populates="instance_permission",
        sa_relationship_kwargs={"cascade": "all,delete,delete-orphan"},
    )
    groups: List["PermissionGroup"] = Relationship(
        link_model=InstancePermissionGroupLink
    )
