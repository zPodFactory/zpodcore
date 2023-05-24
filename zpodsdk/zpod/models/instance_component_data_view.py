from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="InstanceComponentDataView")


@attr.s(auto_attribs=True)
class InstanceComponentDataView:
    """
    Attributes:
        last_octet (Union[Unset, int]):  Example: 11.
    """

    last_octet: Union[Unset, int] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        last_octet = self.last_octet

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if last_octet is not UNSET:
            field_dict["last_octet"] = last_octet

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        last_octet = d.pop("last_octet", UNSET)

        instance_component_data_view = cls(
            last_octet=last_octet,
        )

        return instance_component_data_view
