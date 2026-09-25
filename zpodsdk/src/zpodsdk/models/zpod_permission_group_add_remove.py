from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ZpodPermissionGroupAddRemove")


@_attrs_define
class ZpodPermissionGroupAddRemove:
    """
    Attributes:
        group_id (int | None | Unset):
        groupname (None | str | Unset):
    """

    group_id: int | None | Unset = UNSET
    groupname: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        group_id: int | None | Unset
        if isinstance(self.group_id, Unset):
            group_id = UNSET
        else:
            group_id = self.group_id

        groupname: None | str | Unset
        if isinstance(self.groupname, Unset):
            groupname = UNSET
        else:
            groupname = self.groupname

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if group_id is not UNSET:
            field_dict["group_id"] = group_id
        if groupname is not UNSET:
            field_dict["groupname"] = groupname

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_group_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        group_id = _parse_group_id(d.pop("group_id", UNSET))

        def _parse_groupname(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        groupname = _parse_groupname(d.pop("groupname", UNSET))

        zpod_permission_group_add_remove = cls(
            group_id=group_id,
            groupname=groupname,
        )

        return zpod_permission_group_add_remove
