from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.endpoints_update import EndpointsUpdate


T = TypeVar("T", bound="EndpointUpdate")


@_attrs_define
class EndpointUpdate:
    """
    Attributes:
        endpoints (EndpointsUpdate):
        description (Union[None, Unset, str]):
        enabled (Union[None, Unset, bool]):
    """

    endpoints: "EndpointsUpdate"
    description: Union[None, Unset, str] = UNSET
    enabled: Union[None, Unset, bool] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        endpoints = self.endpoints.to_dict()

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        enabled: Union[None, Unset, bool]
        if isinstance(self.enabled, Unset):
            enabled = UNSET
        else:
            enabled = self.enabled

        field_dict: Dict[str, Any] = {}
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

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_enabled(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        enabled = _parse_enabled(d.pop("enabled", UNSET))

        endpoint_update = cls(
            endpoints=endpoints,
            description=description,
            enabled=enabled,
        )

        return endpoint_update
