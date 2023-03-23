from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="ComponentViewFull")


@attr.s(auto_attribs=True)
class ComponentViewFull:
    """
    Attributes:
        component_name (str):  Example: vcda.
        component_uid (str):  Example: vcda-4.4.1.
        component_version (str):  Example: 4.4.1.
        enabled (Union[Unset, bool]):
        filename (Union[Unset, str]):  Example: vmware_nsx/vmware-nsxt-4.0.1.1.json.
        library_name (Union[Unset, str]):
        status (Union[Unset, str]):  Example: SCHEDULED.
    """

    component_name: str
    component_uid: str
    component_version: str
    enabled: Union[Unset, bool] = False
    filename: Union[Unset, str] = UNSET
    library_name: Union[Unset, str] = UNSET
    status: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        component_name = self.component_name
        component_uid = self.component_uid
        component_version = self.component_version
        enabled = self.enabled
        filename = self.filename
        library_name = self.library_name
        status = self.status

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "component_name": component_name,
                "component_uid": component_uid,
                "component_version": component_version,
            }
        )
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if filename is not UNSET:
            field_dict["filename"] = filename
        if library_name is not UNSET:
            field_dict["library_name"] = library_name
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        component_name = d.pop("component_name")

        component_uid = d.pop("component_uid")

        component_version = d.pop("component_version")

        enabled = d.pop("enabled", UNSET)

        filename = d.pop("filename", UNSET)

        library_name = d.pop("library_name", UNSET)

        status = d.pop("status", UNSET)

        component_view_full = cls(
            component_name=component_name,
            component_uid=component_uid,
            component_version=component_version,
            enabled=enabled,
            filename=filename,
            library_name=library_name,
            status=status,
        )

        component_view_full.additional_properties = d
        return component_view_full

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
