from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="UserView")


@_attrs_define
class UserView:
    """
    Attributes:
        email (str):
        id (int):
        username (str):
    """

    email: str
    id: int
    username: str

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        id = self.id

        username = self.username

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "email": email,
                "id": id,
                "username": username,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        email = d.pop("email")

        id = d.pop("id")

        username = d.pop("username")

        user_view = cls(
            email=email,
            id=id,
            username=username,
        )

        return user_view
