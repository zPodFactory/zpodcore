from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.endpoints_update import EndpointsUpdate


T = TypeVar("T", bound="EndpointUpdate")


@attr.s(auto_attribs=True)
class EndpointUpdate:
    """
    Attributes:
        description (Union[Unset, str]):  Example: current testing env.
        enabled (Union[Unset, bool]):  Example: True.
        endpoints (Union[Unset, EndpointsUpdate]):
    """

    description: Union[Unset, str] = UNSET
    enabled: Union[Unset, bool] = UNSET
    endpoints: Union[Unset, "EndpointsUpdate"] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        description = self.description
        enabled = self.enabled
        endpoints: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.endpoints, Unset):
            endpoints = self.endpoints.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if description is not UNSET:
            field_dict["description"] = description
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if endpoints is not UNSET:
            field_dict["endpoints"] = endpoints

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.endpoints_update import EndpointsUpdate

        d = src_dict.copy()
        description = d.pop("description", UNSET)

        enabled = d.pop("enabled", UNSET)

        _endpoints = d.pop("endpoints", UNSET)
        endpoints: Union[Unset, EndpointsUpdate]
        if isinstance(_endpoints, Unset):
            endpoints = UNSET
        else:
            endpoints = EndpointsUpdate.from_dict(_endpoints)

        endpoint_update = cls(
            description=description,
            enabled=enabled,
            endpoints=endpoints,
        )

        return endpoint_update
