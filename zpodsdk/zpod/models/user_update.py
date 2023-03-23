from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserUpdate")


@attr.s(auto_attribs=True)
class UserUpdate:
    """
    Example:
        {'description': 'Sample User', 'ssh_key': 'xxx', 'superadmin': False}

    Attributes:
        description (Union[Unset, str]):
        id (Union[Unset, int]):
        ssh_key (Union[Unset, str]):
        superadmin (Union[Unset, bool]):
    """

    description: Union[Unset, str] = UNSET
    id: Union[Unset, int] = UNSET
    ssh_key: Union[Unset, str] = UNSET
    superadmin: Union[Unset, bool] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        description = self.description
        id = self.id
        ssh_key = self.ssh_key
        superadmin = self.superadmin

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if description is not UNSET:
            field_dict["description"] = description
        if id is not UNSET:
            field_dict["id"] = id
        if ssh_key is not UNSET:
            field_dict["ssh_key"] = ssh_key
        if superadmin is not UNSET:
            field_dict["superadmin"] = superadmin

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        description = d.pop("description", UNSET)

        id = d.pop("id", UNSET)

        ssh_key = d.pop("ssh_key", UNSET)

        superadmin = d.pop("superadmin", UNSET)

        user_update = cls(
            description=description,
            id=id,
            ssh_key=ssh_key,
            superadmin=superadmin,
        )

        return user_update
