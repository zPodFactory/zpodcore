from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..models.endpoint_status import EndpointStatus

if TYPE_CHECKING:
    from ..models.endpoints_view import EndpointsView


T = TypeVar("T", bound="EndpointViewFull")


@_attrs_define
class EndpointViewFull:
    """
    Attributes:
        description (str):
        endpoints (EndpointsView):
        id (int):
        name (str):
        status (EndpointStatus):
    """

    description: str
    endpoints: EndpointsView
    id: int
    name: str
    status: EndpointStatus

    def to_dict(self) -> dict[str, Any]:
        description = self.description

        endpoints = self.endpoints.to_dict()

        id = self.id

        name = self.name

        status = self.status.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "description": description,
                "endpoints": endpoints,
                "id": id,
                "name": name,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.endpoints_view import EndpointsView

        d = dict(src_dict)
        description = d.pop("description")

        endpoints = EndpointsView.from_dict(d.pop("endpoints"))

        id = d.pop("id")

        name = d.pop("name")

        status = EndpointStatus(d.pop("status"))

        endpoint_view_full = cls(
            description=description,
            endpoints=endpoints,
            id=id,
            name=name,
            status=status,
        )

        return endpoint_view_full
