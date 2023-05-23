from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar

import attr

if TYPE_CHECKING:
    from ..models.instance_component_data_create import InstanceComponentDataCreate


T = TypeVar("T", bound="InstanceComponentCreate")


@attr.s(auto_attribs=True)
class InstanceComponentCreate:
    """
    Attributes:
        component_uid (str):  Example: vcda-4.4.1.
        data (InstanceComponentDataCreate):
    """

    component_uid: str
    data: "InstanceComponentDataCreate"

    def to_dict(self) -> Dict[str, Any]:
        component_uid = self.component_uid
        data = self.data.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "component_uid": component_uid,
                "data": data,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.instance_component_data_create import InstanceComponentDataCreate

        d = src_dict.copy()
        component_uid = d.pop("component_uid")

        data = InstanceComponentDataCreate.from_dict(d.pop("data"))

        instance_component_create = cls(
            component_uid=component_uid,
            data=data,
        )

        return instance_component_create
