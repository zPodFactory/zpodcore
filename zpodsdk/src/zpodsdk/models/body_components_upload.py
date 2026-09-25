from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from .. import types

T = TypeVar("T", bound="BodyComponentsUpload")


@_attrs_define
class BodyComponentsUpload:
    """
    Attributes:
        file (str):
        file_size (int):
        filename (str):
        offset (int):
    """

    file: str
    file_size: int
    filename: str
    offset: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file = self.file

        file_size = self.file_size

        filename = self.filename

        offset = self.offset

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "file": file,
                "file_size": file_size,
                "filename": filename,
                "offset": offset,
            }
        )

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(("file", (None, str(self.file).encode(), "text/plain")))

        files.append(("file_size", (None, str(self.file_size).encode(), "text/plain")))

        files.append(("filename", (None, str(self.filename).encode(), "text/plain")))

        files.append(("offset", (None, str(self.offset).encode(), "text/plain")))

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file = d.pop("file")

        file_size = d.pop("file_size")

        filename = d.pop("filename")

        offset = d.pop("offset")

        body_components_upload = cls(
            file=file,
            file_size=file_size,
            filename=filename,
            offset=offset,
        )

        body_components_upload.additional_properties = d
        return body_components_upload

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
