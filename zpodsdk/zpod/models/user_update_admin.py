from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserUpdateAdmin")


@attr.s(auto_attribs=True)
class UserUpdateAdmin:
    """
    Attributes:
        description (Union[Unset, str]):  Example: Sample User.
        ssh_key (Union[Unset, str]):  Example: <key>.
        superadmin (Union[Unset, bool]):
    """

    description: Union[Unset, str] = UNSET
    ssh_key: Union[Unset, str] = UNSET
    superadmin: Union[Unset, bool] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        description = self.description
        ssh_key = self.ssh_key
        superadmin = self.superadmin

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
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
        description = d.pop("description", UNSET)

        ssh_key = d.pop("ssh_key", UNSET)

        superadmin = d.pop("superadmin", UNSET)

        user_update_admin = cls(
            description=description,
            ssh_key=ssh_key,
            superadmin=superadmin,
        )

        return user_update_admin
