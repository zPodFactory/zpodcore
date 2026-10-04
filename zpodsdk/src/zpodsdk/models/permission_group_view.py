from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.user_view import UserView


T = TypeVar("T", bound="PermissionGroupView")


@_attrs_define
class PermissionGroupView:
    """
    Attributes:
        id (int):
        name (str):
        users (list[UserView]):
    """

    id: int
    name: str
    users: list[UserView]

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        users = []
        for users_item_data in self.users:
            users_item = users_item_data.to_dict()
            users.append(users_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "name": name,
                "users": users,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.user_view import UserView

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        users = []
        _users = d.pop("users")
        for users_item_data in _users:
            users_item = UserView.from_dict(users_item_data)

            users.append(users_item)

        permission_group_view = cls(
            id=id,
            name=name,
            users=users,
        )

        return permission_group_view
