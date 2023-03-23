from typing import TYPE_CHECKING, List

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .instance_models import InstancePermission
    from .user_models import User


class PermissionGroup(SQLModel, table=True):
    __tablename__ = "permission_groups"

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
    )
    name: str = Field(
        default=...,
        nullable=False,
    )

    instance_permissions: List["InstancePermission"] = Relationship(
        back_populates="groups",
        sa_relationship_kwargs=dict(
            secondary="instance_permission_group_link",
        ),
    )
    users: List["User"] = Relationship(
        back_populates="permission_groups",
        sa_relationship_kwargs=dict(
            secondary="permission_group_user_link",
        ),
    )


class PermissionGroupUserLink(SQLModel, table=True):
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
