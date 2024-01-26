from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.endpoints_view import EndpointsView


T = TypeVar("T", bound="EndpointViewFull")


@_attrs_define
class EndpointViewFull:
    """
    Attributes:
        description (str):
        enabled (bool):
        endpoints (EndpointsView):
        id (int):
        name (str):
    """

    description: str
    enabled: bool
    endpoints: "EndpointsView"
    id: int
    name: str

    def to_dict(self) -> Dict[str, Any]:
        description = self.description

        enabled = self.enabled

        endpoints = self.endpoints.to_dict()

        id = self.id

        name = self.name

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "description": description,
                "enabled": enabled,
                "endpoints": endpoints,
                "id": id,
                "name": name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.endpoints_view import EndpointsView

        d = src_dict.copy()
        description = d.pop("description")

        enabled = d.pop("enabled")

        endpoints = EndpointsView.from_dict(d.pop("endpoints"))

        id = d.pop("id")

        name = d.pop("name")

        endpoint_view_full = cls(
            description=description,
            enabled=enabled,
            endpoints=endpoints,
            id=id,
            name=name,
        )

        return endpoint_view_full
