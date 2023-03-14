# from typing import TYPE_CHECKING, List

# from sqlmodel import Field, Relationship, SQLModel

# from .link_models import PermissionGroupUserLink

# if TYPE_CHECKING:
#     from .instance_models import User


# class PermissionGroup(SQLModel, table=True):
#     __tablename__ = "permission_groups"

#     id: int | None = Field(
#         default=None,
#         primary_key=True,
#         nullable=False,
#     )

#     name: str = Field(
#         default=...,
#         nullable=False,
#     )

#     user_links: List["PermissionGroupUserLink"] = Relationship(
#         back_populates="permission_group",
#         sa_relationship_kwargs={"cascade": "all,delete,delete-orphan"},
#     )
#     users: List["User"] = Relationship(
#         link_model=PermissionGroupUserLink,
#         sa_relationship_kwargs=dict(viewonly=True),
#     )
