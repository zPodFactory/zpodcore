from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
    from ..models.endpoint_compute_view import EndpointComputeView
    from ..models.endpoint_network_view import EndpointNetworkView


T = TypeVar("T", bound="EndpointsView")


@attr.s(auto_attribs=True)
class EndpointsView:
    """
    Attributes:
        compute (EndpointComputeView):
        network (EndpointNetworkView):
    """

    compute: "EndpointComputeView"
    network: "EndpointNetworkView"
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        compute = self.compute.to_dict()

        network = self.network.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "compute": compute,
                "network": network,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.endpoint_compute_view import EndpointComputeView
        from ..models.endpoint_network_view import EndpointNetworkView

        d = src_dict.copy()
        compute = EndpointComputeView.from_dict(d.pop("compute"))

        network = EndpointNetworkView.from_dict(d.pop("network"))

        endpoints_view = cls(
            compute=compute,
            network=network,
        )

        endpoints_view.additional_properties = d
        return endpoints_view

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
