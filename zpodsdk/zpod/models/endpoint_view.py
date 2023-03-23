from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
    from ..models.endpoints_view import EndpointsView


T = TypeVar("T", bound="EndpointView")


@attr.s(auto_attribs=True)
class EndpointView:
    """
    Attributes:
        description (str):  Example: current testing env.
        enabled (bool):
        endpoints (EndpointsView):
        name (str):  Example: mylab.
    """

    description: str
    enabled: bool
    endpoints: "EndpointsView"
    name: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        description = self.description
        enabled = self.enabled
        endpoints = self.endpoints.to_dict()

        name = self.name

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "description": description,
                "enabled": enabled,
                "endpoints": endpoints,
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

        name = d.pop("name")

        endpoint_view = cls(
            description=description,
            enabled=enabled,
            endpoints=endpoints,
            name=name,
        )

        endpoint_view.additional_properties = d
        return endpoint_view

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
