from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar

import attr

if TYPE_CHECKING:
    from ..models.endpoints_view import EndpointsView


T = TypeVar("T", bound="EndpointView")


@attr.s(auto_attribs=True)
class EndpointView:
    """
    Attributes:
        description (str):  Example: current testing env.
        enabled (bool):  Example: True.
        endpoints (EndpointsView):
        id (str):  Example: 1.
        name (str):  Example: mylab.
    """

    description: str
    enabled: bool
    endpoints: "EndpointsView"
    id: str
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

        endpoint_view = cls(
            description=description,
            enabled=enabled,
            endpoints=endpoints,
            id=id,
            name=name,
        )

        return endpoint_view
