from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Type,
    TypeVar,
    Union,
    cast,
)

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.endpoints_update import EndpointsUpdate


T = TypeVar("T", bound="EndpointUpdate")


@_attrs_define
class EndpointUpdate:
    """
    Attributes:
        description (Union[None, Unset, str]):
        endpoints (Union['EndpointsUpdate', None, Unset]):
        name (Union[None, Unset, str]):
    """

    description: Union[None, Unset, str] = UNSET
    endpoints: Union["EndpointsUpdate", None, Unset] = UNSET
    name: Union[None, Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        from ..models.endpoints_update import EndpointsUpdate

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        endpoints: Union[Dict[str, Any], None, Unset]
        if isinstance(self.endpoints, Unset):
            endpoints = UNSET
        elif isinstance(self.endpoints, EndpointsUpdate):
            endpoints = self.endpoints.to_dict()
        else:
            endpoints = self.endpoints

        name: Union[None, Unset, str]
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if description is not UNSET:
            field_dict["description"] = description
        if endpoints is not UNSET:
            field_dict["endpoints"] = endpoints
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.endpoints_update import EndpointsUpdate

        d = src_dict.copy()

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_endpoints(data: object) -> Union["EndpointsUpdate", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                endpoints_type_0 = EndpointsUpdate.from_dict(data)

                return endpoints_type_0
            except:  # noqa: E722
                pass
            return cast(Union["EndpointsUpdate", None, Unset], data)

        endpoints = _parse_endpoints(d.pop("endpoints", UNSET))

        def _parse_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        name = _parse_name(d.pop("name", UNSET))

        endpoint_update = cls(
            description=description,
            endpoints=endpoints,
            name=name,
        )

        return endpoint_update
