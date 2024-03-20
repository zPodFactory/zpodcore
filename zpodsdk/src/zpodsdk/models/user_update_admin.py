from typing import Any, Dict, Type, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserUpdateAdmin")


@_attrs_define
class UserUpdateAdmin:
    """
    Attributes:
        description (Union[None, Unset, str]):
        ssh_key (Union[None, Unset, str]):
        superadmin (Union[None, Unset, bool]):
    """

    description: Union[None, Unset, str] = UNSET
    ssh_key: Union[None, Unset, str] = UNSET
    superadmin: Union[None, Unset, bool] = UNSET

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

        superadmin: Union[None, Unset, bool]
        if isinstance(self.superadmin, Unset):
            superadmin = UNSET
        else:
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

        def _parse_superadmin(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        superadmin = _parse_superadmin(d.pop("superadmin", UNSET))

        user_update_admin = cls(
            description=description,
            ssh_key=ssh_key,
            superadmin=superadmin,
        )

        return user_update_admin
