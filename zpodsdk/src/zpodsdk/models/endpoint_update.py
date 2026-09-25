from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.endpoints_update import EndpointsUpdate


T = TypeVar("T", bound="EndpointUpdate")


@_attrs_define
class EndpointUpdate:
    """
    Attributes:
        description (None | str | Unset):
        endpoints (EndpointsUpdate | None | Unset):
        name (None | str | Unset):
    """

    description: None | str | Unset = UNSET
    endpoints: EndpointsUpdate | None | Unset = UNSET
    name: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.endpoints_update import EndpointsUpdate

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        endpoints: dict[str, Any] | None | Unset
        if isinstance(self.endpoints, Unset):
            endpoints = UNSET
        elif isinstance(self.endpoints, EndpointsUpdate):
            endpoints = self.endpoints.to_dict()
        else:
            endpoints = self.endpoints

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if description is not UNSET:
            field_dict["description"] = description
        if endpoints is not UNSET:
            field_dict["endpoints"] = endpoints
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.endpoints_update import EndpointsUpdate

        d = dict(src_dict)

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_endpoints(data: object) -> EndpointsUpdate | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                endpoints_type_0 = EndpointsUpdate.from_dict(data)

                return endpoints_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(EndpointsUpdate | None | Unset, data)

        endpoints = _parse_endpoints(d.pop("endpoints", UNSET))

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        endpoint_update = cls(
            description=description,
            endpoints=endpoints,
            name=name,
        )

        return endpoint_update
