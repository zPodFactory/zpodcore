from typing import Any, Dict, Type, TypeVar

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

    def to_dict(self) -> Dict[str, Any]:
        email = self.email
        id = self.id
        username = self.username

        field_dict: Dict[str, Any] = {}
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

        return user_view
