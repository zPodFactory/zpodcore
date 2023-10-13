from typing import TYPE_CHECKING, List

from sqlmodel import JSON, Column, Field, Relationship

from zpodcommon import enums
from zpodcommon.models.model_base import ModelBase

if TYPE_CHECKING:
    from .permission_group_models import PermissionGroup
    from .user_models import User


class Endpoint(ModelBase, table=True):
    __tablename__ = "endpoints"

    id: int | None = Field(default=None, primary_key=True, nullable=False)
    name: str = Field(..., unique=True, index=True, nullable=False)
    description: str = Field("", nullable=False)
    endpoints: dict = Field(sa_column=Column(JSON))
    enabled: bool = Field(False, nullable=False)

    permissions: List["EndpointPermission"] = Relationship(
        back_populates="endpoint",
        sa_relationship_kwargs={
            "cascade": "all,delete,delete-orphan",
        },
    )


class EndpointPermission(ModelBase, table=True):
    __tablename__ = "endpoint_permissions"

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
    )
    permission: enums.EndpointPermission = Field(
        default=...,
        nullable=False,
    )
    endpoint_id: int = Field(
        default=...,
        nullable=False,
        foreign_key="endpoints.id",
    )

    endpoint: "Endpoint" = Relationship(back_populates="permissions")
    users: List["User"] = Relationship(
        back_populates="endpoint_permissions",
        sa_relationship_kwargs=dict(
            secondary="endpoint_permission_user_link",
        ),
    )
    permission_groups: List["PermissionGroup"] = Relationship(
        back_populates="endpoint_permissions",
        sa_relationship_kwargs=dict(
            secondary="endpoint_permission_group_link",
        ),
    )


class EndpointPermissionUserLink(ModelBase, table=True):
    __tablename__ = "endpoint_permission_user_link"

    endpoint_permission_id: int = Field(
        default=...,
        primary_key=True,
        nullable=False,
        foreign_key="endpoint_permissions.id",
    )
    user_id: int = Field(
        default=...,
        primary_key=True,
        nullable=False,
        foreign_key="users.id",
    )


class EndpointPermissionGroupLink(ModelBase, table=True):
    __tablename__ = "endpoint_permission_group_link"

    endpoint_permission_id: int = Field(
        default=...,
        primary_key=True,
        nullable=False,
        foreign_key="endpoint_permissions.id",
    )
    permission_group_id: int = Field(
        default=...,
        primary_key=True,
        nullable=False,
        foreign_key="permission_groups.id",
    )
