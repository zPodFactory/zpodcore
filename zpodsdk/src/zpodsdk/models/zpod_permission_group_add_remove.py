from typing import Any, Dict, Type, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ZpodPermissionGroupAddRemove")


@_attrs_define
class ZpodPermissionGroupAddRemove:
    """
    Attributes:
        group_id (Union[None, Unset, int]):
        groupname (Union[None, Unset, str]):
    """

    group_id: Union[None, Unset, int] = UNSET
    groupname: Union[None, Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        group_id: Union[None, Unset, int]
        if isinstance(self.group_id, Unset):
            group_id = UNSET
        else:
            group_id = self.group_id

        groupname: Union[None, Unset, str]
        if isinstance(self.groupname, Unset):
            groupname = UNSET
        else:
            groupname = self.groupname

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if group_id is not UNSET:
            field_dict["group_id"] = group_id
        if groupname is not UNSET:
            field_dict["groupname"] = groupname

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()

        def _parse_group_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        group_id = _parse_group_id(d.pop("group_id", UNSET))

        def _parse_groupname(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        groupname = _parse_groupname(d.pop("groupname", UNSET))

        zpod_permission_group_add_remove = cls(
            group_id=group_id,
            groupname=groupname,
        )

        return zpod_permission_group_add_remove
