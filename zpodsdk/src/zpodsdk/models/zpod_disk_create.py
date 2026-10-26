from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="ZpodDiskCreate")


@_attrs_define
class ZpodDiskCreate:
    """
    Attributes:
        size_gb (int):
    """

    size_gb: int

    def to_dict(self) -> dict[str, Any]:
        size_gb = self.size_gb

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "size_gb": size_gb,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        size_gb = d.pop("size_gb")

        zpod_disk_create = cls(
            size_gb=size_gb,
        )

        return zpod_disk_create
