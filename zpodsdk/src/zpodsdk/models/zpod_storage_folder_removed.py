from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ZpodStorageFolderRemoved")


@_attrs_define
class ZpodStorageFolderRemoved:
    """
    Attributes:
        forced (bool):
        message (str):
        path (str):
        removed (int):
    """

    forced: bool
    message: str
    path: str
    removed: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        forced = self.forced

        message = self.message

        path = self.path

        removed = self.removed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "forced": forced,
                "message": message,
                "path": path,
                "removed": removed,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        forced = d.pop("forced")

        message = d.pop("message")

        path = d.pop("path")

        removed = d.pop("removed")

        zpod_storage_folder_removed = cls(
            forced=forced,
            message=message,
            path=path,
            removed=removed,
        )

        zpod_storage_folder_removed.additional_properties = d
        return zpod_storage_folder_removed

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
