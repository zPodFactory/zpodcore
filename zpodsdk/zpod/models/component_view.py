from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="ComponentView")


@attr.s(auto_attribs=True)
class ComponentView:
    """
    Attributes:
        enabled (bool):
        filename (str):  Example: vmware_nsx/vmware-nsxt-4.0.1.1.json.
        library_name (Union[Unset, str]):
    """

    enabled: bool
    filename: str
    library_name: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        enabled = self.enabled
        filename = self.filename
        library_name = self.library_name

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "enabled": enabled,
                "filename": filename,
            }
        )
        if library_name is not UNSET:
            field_dict["library_name"] = library_name

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        enabled = d.pop("enabled")

        filename = d.pop("filename")

        library_name = d.pop("library_name", UNSET)

        component_view = cls(
            enabled=enabled,
            filename=filename,
            library_name=library_name,
        )

        component_view.additional_properties = d
        return component_view

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
