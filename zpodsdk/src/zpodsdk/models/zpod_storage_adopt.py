from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ZpodStorageAdopt")


@_attrs_define
class ZpodStorageAdopt:
    """
    Attributes:
        device (str):
        name (None | str | Unset):
    """

    device: str
    name: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        device = self.device

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "device": device,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        device = d.pop("device")

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        zpod_storage_adopt = cls(
            device=device,
            name=name,
        )

        return zpod_storage_adopt
