from typing import Any, Dict, Type, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserCreate")


@_attrs_define
class UserCreate:
    """
    Attributes:
        email (str):
        username (str):
        description (Union[Unset, str]):  Default: ''.
        ssh_key (Union[Unset, str]):  Default: ''.
        superadmin (Union[Unset, bool]):  Default: False.
    """

    email: str
    username: str
    description: Union[Unset, str] = ""
    ssh_key: Union[Unset, str] = ""
    superadmin: Union[Unset, bool] = False

    def to_dict(self) -> Dict[str, Any]:
        email = self.email

        username = self.username

        description = self.description

        ssh_key = self.ssh_key

        superadmin = self.superadmin

        field_dict: Dict[str, Any] = {}
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
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
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
