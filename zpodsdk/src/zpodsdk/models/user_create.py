from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserCreate")


@_attrs_define
class UserCreate:
    """
    Attributes:
        email (str):
        username (str):
        description (str | Unset):  Default: ''.
        ssh_key (str | Unset):  Default: ''.
        superadmin (bool | Unset):  Default: False.
    """

    email: str
    username: str
    description: str | Unset = ""
    ssh_key: str | Unset = ""
    superadmin: bool | Unset = False

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        username = self.username

        description = self.description

        ssh_key = self.ssh_key

        superadmin = self.superadmin

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "email": email,
                "username": username,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if ssh_key is not UNSET:
            field_dict["ssh_key"] = ssh_key
        if superadmin is not UNSET:
            field_dict["superadmin"] = superadmin

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        email = d.pop("email")

        username = d.pop("username")

        description = d.pop("description", UNSET)

        ssh_key = d.pop("ssh_key", UNSET)

        superadmin = d.pop("superadmin", UNSET)

        user_create = cls(
            email=email,
            username=username,
            description=description,
            ssh_key=ssh_key,
            superadmin=superadmin,
        )

        return user_create
