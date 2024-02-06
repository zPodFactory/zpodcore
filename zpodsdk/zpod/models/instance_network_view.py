from typing import Any, Dict, Type, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="InstanceNetworkView")


@_attrs_define
class InstanceNetworkView:
    """
    Attributes:
        cidr (str):
        id (int):
    """

    cidr: str
    id: int

    def to_dict(self) -> Dict[str, Any]:
        cidr = self.cidr

        id = self.id

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "cidr": cidr,
                "id": id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        cidr = d.pop("cidr")

        id = d.pop("id")

        instance_network_view = cls(
            cidr=cidr,
            id=id,
        )

        return instance_network_view
