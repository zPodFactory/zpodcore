from typing import Any, Dict, Type, TypeVar

import attr

T = TypeVar("T", bound="InstanceComponentCreate")


@attr.s(auto_attribs=True)
class InstanceComponentCreate:
    """
    Attributes:
        component_uid (str):  Example: vcda-4.4.1.
    """

    component_uid: str

    def to_dict(self) -> Dict[str, Any]:
        component_uid = self.component_uid

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "component_uid": component_uid,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        component_uid = d.pop("component_uid")

        instance_component_create = cls(
            component_uid=component_uid,
        )

        return instance_component_create
