from io import BytesIO
from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import File

T = TypeVar("T", bound="BodyComponentsUpload")


@_attrs_define
class BodyComponentsUpload:
    """
    Attributes:
        file (File):
        file_size (int):
        filename (str):
        offset (int):
    """

    file: File
    file_size: int
    filename: str
    offset: int
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        file = self.file.to_tuple()

        file_size = self.file_size

        filename = self.filename

        offset = self.offset

        field_dict: Dict[str, Any] = {}
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

    def to_multipart(self) -> Dict[str, Any]:
        file = self.file.to_tuple()

        file_size = (None, str(self.file_size).encode(), "text/plain")

        filename = (None, str(self.filename).encode(), "text/plain")

        offset = (None, str(self.offset).encode(), "text/plain")

        field_dict: Dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            field_dict[prop_name] = (None, str(prop).encode(), "text/plain")

        field_dict.update(
            {
                "file": file,
                "file_size": file_size,
                "filename": filename,
                "offset": offset,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        file = File(payload=BytesIO(d.pop("file")))

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
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
