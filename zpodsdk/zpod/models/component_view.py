from typing import Any, Dict, Type, TypeVar

import attr

T = TypeVar("T", bound="ComponentView")


@attr.s(auto_attribs=True)
class ComponentView:
    """
    Attributes:
        component_description (str):  Example: VMware Cloud Director Availabilty.
        component_name (str):  Example: vcda.
        component_uid (str):  Example: vcda-4.4.1.
        component_version (str):  Example: 4.4.1.
        id (str):  Example: 1.
    """

    component_description: str
    component_name: str
    component_uid: str
    component_version: str
    id: str

    def to_dict(self) -> Dict[str, Any]:
        component_description = self.component_description
        component_name = self.component_name
        component_uid = self.component_uid
        component_version = self.component_version
        id = self.id

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "component_description": component_description,
                "component_name": component_name,
                "component_uid": component_uid,
                "component_version": component_version,
                "id": id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        component_description = d.pop("component_description")

        component_name = d.pop("component_name")

        component_uid = d.pop("component_uid")

        component_version = d.pop("component_version")

        id = d.pop("id")

        component_view = cls(
            component_description=component_description,
            component_name=component_name,
            component_uid=component_uid,
            component_version=component_version,
            id=id,
        )

        return component_view
