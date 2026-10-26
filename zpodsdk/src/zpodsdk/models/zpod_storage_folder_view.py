from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ZpodStorageFolderView")


@_attrs_define
class ZpodStorageFolderView:
    """
    Attributes:
        empty (bool):
        exported (bool):
        mode (str):
        name (str):
        owner (str):
        path (str):
        protected (bool):
    """

    empty: bool
    exported: bool
    mode: str
    name: str
    owner: str
    path: str
    protected: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        empty = self.empty

        exported = self.exported

        mode = self.mode

        name = self.name

        owner = self.owner

        path = self.path

        protected = self.protected

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "empty": empty,
                "exported": exported,
                "mode": mode,
                "name": name,
                "owner": owner,
                "path": path,
                "protected": protected,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        empty = d.pop("empty")

        exported = d.pop("exported")

        mode = d.pop("mode")

        name = d.pop("name")

        owner = d.pop("owner")

        path = d.pop("path")

        protected = d.pop("protected")

        zpod_storage_folder_view = cls(
            empty=empty,
            exported=exported,
            mode=mode,
            name=name,
            owner=owner,
            path=path,
            protected=protected,
        )

        zpod_storage_folder_view.additional_properties = d
        return zpod_storage_folder_view

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
