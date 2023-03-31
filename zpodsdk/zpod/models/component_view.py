from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="ComponentView")


@attr.s(auto_attribs=True)
class ComponentView:
    """
    Attributes:
        component_name (str):  Example: vcda.
        component_uid (str):  Example: vcda-4.4.1.
        component_version (str):  Example: 4.4.1.
        component_description (Union[Unset, str]):  Example: VMWare NSX.
    """

    component_name: str
    component_uid: str
    component_version: str
    component_description: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        component_name = self.component_name
        component_uid = self.component_uid
        component_version = self.component_version
        component_description = self.component_description

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "component_name": component_name,
                "component_uid": component_uid,
                "component_version": component_version,
            }
        )
        if component_description is not UNSET:
            field_dict["component_description"] = component_description

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        component_name = d.pop("component_name")

        component_uid = d.pop("component_uid")

        component_version = d.pop("component_version")

        component_description = d.pop("component_description", UNSET)

        component_view = cls(
            component_name=component_name,
            component_uid=component_uid,
            component_version=component_version,
            component_description=component_description,
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
