from datetime import datetime
from typing import TYPE_CHECKING, List

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

from .link_models import InstancePermissionUserLink

if TYPE_CHECKING:
    from .instance_models import InstancePermission

from .mixins import CommonDatesMixin


class User(CommonDatesMixin, SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True, nullable=False)
    username: str = Field(..., unique=True, index=True, nullable=False)
    email: EmailStr = Field(..., unique=True, index=True, nullable=False)
    description: str = Field("", nullable=False)
    api_token: str = Field("", index=True, nullable=False)
    ssh_key: str = Field("", nullable=False)
    last_connection_date: datetime = Field(None)
    superadmin: bool = Field(False, nullable=False)

    instance_permission_links: List["InstancePermissionUserLink"] = Relationship(
        back_populates="user",
    )
    instance_permissions: List["InstancePermission"] = Relationship(
        back_populates="users", link_model=InstancePermissionUserLink
    )
