from typing import TYPE_CHECKING, List

from sqlmodel import Field, Relationship

from zpodcommon.models.model_base import ModelBase

if TYPE_CHECKING:
    from .endpoint_models import EndpointPermission
    from .user_models import User
    from .zpod_models import ZpodPermission


class PermissionGroup(ModelBase, table=True):
    __tablename__ = "permission_groups"

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
    )
    name: str = Field(
        default=...,
        nullable=False,
        unique=True,
    )

    endpoint_permissions: List["EndpointPermission"] = Relationship(
        back_populates="permission_groups",
        sa_relationship_kwargs={
            "secondary": "endpoint_permission_group_link",
        },
    )

    zpod_permissions: List["ZpodPermission"] = Relationship(
        back_populates="permission_groups",
        sa_relationship_kwargs={
            "secondary": "zpod_permission_group_link",
        },
    )
    users: List["User"] = Relationship(
        back_populates="permission_groups",
        sa_relationship_kwargs={
            "secondary": "permission_group_user_link",
        },
    )


class PermissionGroupUserLink(ModelBase, table=True):
    __tablename__ = "permission_group_user_link"

    permission_group_id: int = Field(
        default=...,
        primary_key=True,
        nullable=False,
        foreign_key="permission_groups.id",
    )
    user_id: int = Field(
        default=...,
        primary_key=True,
        nullable=False,
        foreign_key="users.id",
    )
