from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.endpoint_compute_view import EndpointComputeView
    from ..models.endpoint_network_view import EndpointNetworkView


T = TypeVar("T", bound="EndpointsView")


@_attrs_define
class EndpointsView:
    """
    Attributes:
        compute (EndpointComputeView):
        network (EndpointNetworkView):
    """

    compute: "EndpointComputeView"
    network: "EndpointNetworkView"

    def to_dict(self) -> Dict[str, Any]:
        compute = self.compute.to_dict()

        network = self.network.to_dict()

        field_dict: Dict[str, Any] = {}
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

        return endpoints_view
