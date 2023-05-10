from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="InstanceComponentDataCreate")


@attr.s(auto_attribs=True)
class InstanceComponentDataCreate:
    """
    Attributes:
        mgmt_ip (Union[Unset, int]):  Example: 11.
    """

    mgmt_ip: Union[Unset, int] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        mgmt_ip = self.mgmt_ip

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if mgmt_ip is not UNSET:
            field_dict["mgmt_ip"] = mgmt_ip

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        mgmt_ip = d.pop("mgmt_ip", UNSET)

        instance_component_data_create = cls(
            mgmt_ip=mgmt_ip,
        )

        return instance_component_data_create
