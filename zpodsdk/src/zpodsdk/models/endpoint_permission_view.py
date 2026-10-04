from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..models.endpoint_permission import EndpointPermission
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.permission_group_view import PermissionGroupView
    from ..models.user_view import UserView


T = TypeVar("T", bound="EndpointPermissionView")


@_attrs_define
class EndpointPermissionView:
    """
    Attributes:
        id (int):
        permission (EndpointPermission):
        permission_groups (list[PermissionGroupView] | Unset):
        users (list[UserView] | Unset):
    """

    id: int
    permission: EndpointPermission
    permission_groups: list[PermissionGroupView] | Unset = UNSET
    users: list[UserView] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        permission = self.permission.value

        permission_groups: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.permission_groups, Unset):
            permission_groups = []
            for permission_groups_item_data in self.permission_groups:
                permission_groups_item = permission_groups_item_data.to_dict()
                permission_groups.append(permission_groups_item)

        users: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.users, Unset):
            users = []
            for users_item_data in self.users:
                users_item = users_item_data.to_dict()
                users.append(users_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "permission": permission,
            }
        )
        if permission_groups is not UNSET:
            field_dict["permission_groups"] = permission_groups
        if users is not UNSET:
            field_dict["users"] = users

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.permission_group_view import PermissionGroupView
        from ..models.user_view import UserView

        d = dict(src_dict)
        id = d.pop("id")

        permission = EndpointPermission(d.pop("permission"))

        _permission_groups = d.pop("permission_groups", UNSET)
        permission_groups: list[PermissionGroupView] | Unset = UNSET
        if _permission_groups is not UNSET:
            permission_groups = []
            for permission_groups_item_data in _permission_groups:
                permission_groups_item = PermissionGroupView.from_dict(
                    permission_groups_item_data
                )

                permission_groups.append(permission_groups_item)

        _users = d.pop("users", UNSET)
        users: list[UserView] | Unset = UNSET
        if _users is not UNSET:
            users = []
            for users_item_data in _users:
                users_item = UserView.from_dict(users_item_data)

                users.append(users_item)

        endpoint_permission_view = cls(
            id=id,
            permission=permission,
            permission_groups=permission_groups,
            users=users,
        )

        return endpoint_permission_view
