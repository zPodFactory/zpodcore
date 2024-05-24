from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

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
        permission_groups (Union[Unset, List['PermissionGroupView']]):
        users (Union[Unset, List['UserView']]):
    """

    id: int
    permission: EndpointPermission
    permission_groups: Union[Unset, List["PermissionGroupView"]] = UNSET
    users: Union[Unset, List["UserView"]] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        id = self.id

        permission = self.permission.value

        permission_groups: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.permission_groups, Unset):
            permission_groups = []
            for permission_groups_item_data in self.permission_groups:
                permission_groups_item = permission_groups_item_data.to_dict()
                permission_groups.append(permission_groups_item)

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
        if permission_groups is not UNSET:
            field_dict["permission_groups"] = permission_groups
        if users is not UNSET:
            field_dict["users"] = users

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.permission_group_view import PermissionGroupView
        from ..models.user_view import UserView

        d = src_dict.copy()
        id = d.pop("id")

        permission = EndpointPermission(d.pop("permission"))

        permission_groups = []
        _permission_groups = d.pop("permission_groups", UNSET)
        for permission_groups_item_data in _permission_groups or []:
            permission_groups_item = PermissionGroupView.from_dict(
                permission_groups_item_data
            )

            permission_groups.append(permission_groups_item)

        users = []
        _users = d.pop("users", UNSET)
        for users_item_data in _users or []:
            users_item = UserView.from_dict(users_item_data)

            users.append(users_item)

        endpoint_permission_view = cls(
            id=id,
            permission=permission,
            permission_groups=permission_groups,
            users=users,
        )

        return endpoint_permission_view
