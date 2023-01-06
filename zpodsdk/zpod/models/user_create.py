from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserCreate")


@attr.s(auto_attribs=True)
class UserCreate:
    """
    Attributes:
        description (str):  Example: Sample User.
        email (str):  Example: jdoe@example.com.
        username (str):  Example: jdoe.
        ssh_key (Union[Unset, str]):  Default: ''.
        superadmin (Union[Unset, bool]):
    """

    description: str
    email: str
    username: str
    ssh_key: Union[Unset, str] = ""
    superadmin: Union[Unset, bool] = False

    def to_dict(self) -> Dict[str, Any]:
        description = self.description
        email = self.email
        username = self.username
        ssh_key = self.ssh_key
        superadmin = self.superadmin

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "description": description,
                "email": email,
                "username": username,
            }
        )
        if ssh_key is not UNSET:
            field_dict["ssh_key"] = ssh_key
        if superadmin is not UNSET:
            field_dict["superadmin"] = superadmin

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        description = d.pop("description")

        email = d.pop("email")

        username = d.pop("username")

        ssh_key = d.pop("ssh_key", UNSET)

        superadmin = d.pop("superadmin", UNSET)

        user_create = cls(
            description=description,
            email=email,
            username=username,
            ssh_key=ssh_key,
            superadmin=superadmin,
        )

        return user_create
