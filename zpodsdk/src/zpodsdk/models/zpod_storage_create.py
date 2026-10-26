from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ZpodStorageCreate")


@_attrs_define
class ZpodStorageCreate:
    """
    Attributes:
        disk (str):
        lvm (bool | Unset):  Default: False.
        name (None | str | Unset):
    """

    disk: str
    lvm: bool | Unset = False
    name: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        disk = self.disk

        lvm = self.lvm

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "disk": disk,
            }
        )
        if lvm is not UNSET:
            field_dict["lvm"] = lvm
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        disk = d.pop("disk")

        lvm = d.pop("lvm", UNSET)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        zpod_storage_create = cls(
            disk=disk,
            lvm=lvm,
            name=name,
        )

        return zpod_storage_create
