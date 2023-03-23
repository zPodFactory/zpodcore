from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="UserView")


@attr.s(auto_attribs=True)
class UserView:
    """
    Attributes:
        email (str):  Example: jdoe@example.com.
        id (int):  Example: 1.
        username (str):  Example: jdoe.
    """

    email: str
    id: int
    username: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        email = self.email
        id = self.id
        username = self.username

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "email": email,
                "id": id,
                "username": username,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        email = d.pop("email")

        id = d.pop("id")

        username = d.pop("username")

        user_view = cls(
            email=email,
            id=id,
            username=username,
        )

        user_view.additional_properties = d
        return user_view

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
