from typing import Any, Dict, Type, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserUpdate")


@_attrs_define
class UserUpdate:
    """
    Attributes:
        description (Union[None, Unset, str]):
        ssh_key (Union[None, Unset, str]):
    """

    description: Union[None, Unset, str] = UNSET
    ssh_key: Union[None, Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        ssh_key: Union[None, Unset, str]
        if isinstance(self.ssh_key, Unset):
            ssh_key = UNSET
        else:
            ssh_key = self.ssh_key

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if description is not UNSET:
            field_dict["description"] = description
        if ssh_key is not UNSET:
            field_dict["ssh_key"] = ssh_key

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_ssh_key(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        ssh_key = _parse_ssh_key(d.pop("ssh_key", UNSET))

        user_update = cls(
            description=description,
            ssh_key=ssh_key,
        )

        return user_update
