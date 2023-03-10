from typing import List

from sqlmodel import Field, Relationship, SQLModel

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

    users: List["PermissionGroupUser"] = Relationship(
        back_populates="permission_group",
        sa_relationship_kwargs={"cascade": "all,delete,delete-orphan"},
    )


class PermissionGroupUser(SQLModel, table=True):
    __tablename__ = "permission_group_users"

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

    permission_group: "PermissionGroup" = Relationship(back_populates="users")
    user: "User" = Relationship()
