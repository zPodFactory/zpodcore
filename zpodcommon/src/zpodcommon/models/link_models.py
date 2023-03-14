from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .instance_models import InstancePermission
    from .permission_group_models import PermissionGroup
    from .user_models import User


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
    user: "User" = Relationship(back_populates="instance_permission_links")


# class InstancePermissionGroupLink(SQLModel, table=True):
#     __tablename__ = "instance_permission_group_link"

#     instance_permission_id: int = Field(
#         default=...,
#         primary_key=True,
#         nullable=False,
#         foreign_key="instance_permissions.id",
#     )
#     permission_group_id: int = Field(
#         default=...,
#         primary_key=True,
#         nullable=False,
#         foreign_key="permission_groups.id",
#     )

#     # instance_permission: "InstancePermission" = Relationship(
#     #     back_populates="group_links"
#     # )
#     # user: "PermissionGroup" = Relationship(back_populates="user_links")


# class PermissionGroupUserLink(SQLModel, table=True):
#     __tablename__ = "permission_group_user_link"

#     permission_group_id: int = Field(
#         default=...,
#         primary_key=True,
#         nullable=False,
#         foreign_key="permission_groups.id",
#     )

#     user_id: int = Field(
#         default=...,
#         primary_key=True,
#         nullable=False,
#         foreign_key="users.id",
#     )

#     permission_group: "PermissionGroup" = Relationship(back_populates="user_links")
#     user: "User" = Relationship(back_populates="user_links")
