from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="InstanceNetworkView")


@attr.s(auto_attribs=True)
class InstanceNetworkView:
    """
    Attributes:
        cidr (str):  Example: 1.
        id (int):  Example: 1.
    """

    cidr: str
    id: int
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        cidr = self.cidr
        id = self.id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
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

        instance_network_view.additional_properties = d
        return instance_network_view

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
