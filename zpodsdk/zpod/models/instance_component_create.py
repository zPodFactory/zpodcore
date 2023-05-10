from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.instance_component_data_create import InstanceComponentDataCreate


T = TypeVar("T", bound="InstanceComponentCreate")


@attr.s(auto_attribs=True)
class InstanceComponentCreate:
    """
    Attributes:
        component_uid (str):  Example: vcda-4.4.1.
        data (InstanceComponentDataCreate):
        extra_id (Union[Unset, str]):  Default: ''. Example: 11.
    """

    component_uid: str
    data: "InstanceComponentDataCreate"
    extra_id: Union[Unset, str] = ""

    def to_dict(self) -> Dict[str, Any]:
        component_uid = self.component_uid
        data = self.data.to_dict()

        extra_id = self.extra_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "component_uid": component_uid,
                "data": data,
            }
        )
        if extra_id is not UNSET:
            field_dict["extra_id"] = extra_id

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.instance_component_data_create import InstanceComponentDataCreate

        d = src_dict.copy()
        component_uid = d.pop("component_uid")

        data = InstanceComponentDataCreate.from_dict(d.pop("data"))

        extra_id = d.pop("extra_id", UNSET)

        instance_component_create = cls(
            component_uid=component_uid,
            data=data,
            extra_id=extra_id,
        )

        return instance_component_create
