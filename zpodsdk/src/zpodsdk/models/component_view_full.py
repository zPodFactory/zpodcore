from typing import Any, Dict, Type, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ComponentViewFull")


@_attrs_define
class ComponentViewFull:
    """
    Attributes:
        component_description (str):
        component_name (str):
        component_uid (str):
        component_version (str):
        file_checksum (str):
        filename (str):
        id (int):
        jsonfile (str):
        library_name (str):
        status (str):
        download_status (Union[None, Unset, str]):
    """

    component_description: str
    component_name: str
    component_uid: str
    component_version: str
    file_checksum: str
    filename: str
    id: int
    jsonfile: str
    library_name: str
    status: str
    download_status: Union[None, Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        component_description = self.component_description

        component_name = self.component_name

        component_uid = self.component_uid

        component_version = self.component_version

        file_checksum = self.file_checksum

        filename = self.filename

        id = self.id

        jsonfile = self.jsonfile

        library_name = self.library_name

        status = self.status

        download_status: Union[None, Unset, str]
        if isinstance(self.download_status, Unset):
            download_status = UNSET
        else:
            download_status = self.download_status

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "component_description": component_description,
                "component_name": component_name,
                "component_uid": component_uid,
                "component_version": component_version,
                "file_checksum": file_checksum,
                "filename": filename,
                "id": id,
                "jsonfile": jsonfile,
                "library_name": library_name,
                "status": status,
            }
        )
        if download_status is not UNSET:
            field_dict["download_status"] = download_status

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        component_description = d.pop("component_description")

        component_name = d.pop("component_name")

        component_uid = d.pop("component_uid")

        component_version = d.pop("component_version")

        file_checksum = d.pop("file_checksum")

        filename = d.pop("filename")

        id = d.pop("id")

        jsonfile = d.pop("jsonfile")

        library_name = d.pop("library_name")

        status = d.pop("status")

        def _parse_download_status(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        download_status = _parse_download_status(d.pop("download_status", UNSET))

        component_view_full = cls(
            component_description=component_description,
            component_name=component_name,
            component_uid=component_uid,
            component_version=component_version,
            file_checksum=file_checksum,
            filename=filename,
            id=id,
            jsonfile=jsonfile,
            library_name=library_name,
            status=status,
            download_status=download_status,
        )

        return component_view_full
