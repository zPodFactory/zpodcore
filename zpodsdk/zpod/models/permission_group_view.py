from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
    from ..models.user_view import UserView


T = TypeVar("T", bound="PermissionGroupView")


@attr.s(auto_attribs=True)
class PermissionGroupView:
    """
    Attributes:
        id (int):  Example: 1.
        name (str):  Example: Team.
        users (List['UserView']):
    """

    id: int
    name: str
    users: List["UserView"]
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id
        name = self.name
        users = []
        for users_item_data in self.users:
            users_item = users_item_data.to_dict()

            users.append(users_item)

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "users": users,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.user_view import UserView

        d = src_dict.copy()
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

        permission_group_view.additional_properties = d
        return permission_group_view

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
