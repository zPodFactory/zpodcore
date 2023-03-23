from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.endpoints_update import EndpointsUpdate


T = TypeVar("T", bound="EndpointUpdate")


@attr.s(auto_attribs=True)
class EndpointUpdate:
    """
    Attributes:
        endpoints (EndpointsUpdate):
        description (Union[Unset, str]):  Example: current testing env.
        enabled (Union[Unset, bool]):  Example: True.
    """

    endpoints: "EndpointsUpdate"
    description: Union[Unset, str] = UNSET
    enabled: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        endpoints = self.endpoints.to_dict()

        description = self.description
        enabled = self.enabled

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "endpoints": endpoints,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if enabled is not UNSET:
            field_dict["enabled"] = enabled

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.endpoints_update import EndpointsUpdate

        d = src_dict.copy()
        endpoints = EndpointsUpdate.from_dict(d.pop("endpoints"))

        description = d.pop("description", UNSET)

        enabled = d.pop("enabled", UNSET)

        endpoint_update = cls(
            endpoints=endpoints,
            description=description,
            enabled=enabled,
        )

        endpoint_update.additional_properties = d
        return endpoint_update

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
