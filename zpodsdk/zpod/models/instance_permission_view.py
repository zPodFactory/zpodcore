from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.instance_permission import InstancePermission
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.permission_group_view import PermissionGroupView
    from ..models.user_view import UserView


T = TypeVar("T", bound="InstancePermissionView")


@attr.s(auto_attribs=True)
class InstancePermissionView:
    """
    Attributes:
        id (int):  Example: 1.
        permission (InstancePermission): An enumeration.
        groups (Union[Unset, List['PermissionGroupView']]):
        users (Union[Unset, List['UserView']]):
    """

    id: int
    permission: InstancePermission
    groups: Union[Unset, List["PermissionGroupView"]] = UNSET
    users: Union[Unset, List["UserView"]] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        id = self.id
        permission = self.permission.value

        groups: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.groups, Unset):
            groups = []
            for groups_item_data in self.groups:
                groups_item = groups_item_data.to_dict()

                groups.append(groups_item)

        users: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.users, Unset):
            users = []
            for users_item_data in self.users:
                users_item = users_item_data.to_dict()

                users.append(users_item)

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "id": id,
                "permission": permission,
            }
        )
        if groups is not UNSET:
            field_dict["groups"] = groups
        if users is not UNSET:
            field_dict["users"] = users

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.permission_group_view import PermissionGroupView
        from ..models.user_view import UserView

        d = src_dict.copy()
        id = d.pop("id")

        permission = InstancePermission(d.pop("permission"))

        groups = []
        _groups = d.pop("groups", UNSET)
        for groups_item_data in _groups or []:
            groups_item = PermissionGroupView.from_dict(groups_item_data)

            groups.append(groups_item)

        users = []
        _users = d.pop("users", UNSET)
        for users_item_data in _users or []:
            users_item = UserView.from_dict(users_item_data)

            users.append(users_item)

        instance_permission_view = cls(
            id=id,
            permission=permission,
            groups=groups,
            users=users,
        )

        return instance_permission_view
