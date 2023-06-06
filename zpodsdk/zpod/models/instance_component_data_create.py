from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="InstanceComponentDataCreate")


@attr.s(auto_attribs=True)
class InstanceComponentDataCreate:
    """
    Attributes:
        last_octet (Union[Unset, int]):  Example: 11.
        vcpu (Union[Unset, int]):  Example: 4.
        vmem (Union[Unset, int]):  Example: 16.
    """

    last_octet: Union[Unset, int] = UNSET
    vcpu: Union[Unset, int] = UNSET
    vmem: Union[Unset, int] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        last_octet = self.last_octet
        vcpu = self.vcpu
        vmem = self.vmem

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if last_octet is not UNSET:
            field_dict["last_octet"] = last_octet
        if vcpu is not UNSET:
            field_dict["vcpu"] = vcpu
        if vmem is not UNSET:
            field_dict["vmem"] = vmem

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        last_octet = d.pop("last_octet", UNSET)

        vcpu = d.pop("vcpu", UNSET)

        vmem = d.pop("vmem", UNSET)

        instance_component_data_create = cls(
            last_octet=last_octet,
            vcpu=vcpu,
            vmem=vmem,
        )

        return instance_component_data_create
