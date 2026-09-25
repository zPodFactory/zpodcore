from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

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

    compute: EndpointComputeView
    network: EndpointNetworkView

    def to_dict(self) -> dict[str, Any]:
        compute = self.compute.to_dict()

        network = self.network.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "compute": compute,
                "network": network,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.endpoint_compute_view import EndpointComputeView
        from ..models.endpoint_network_view import EndpointNetworkView

        d = dict(src_dict)
        compute = EndpointComputeView.from_dict(d.pop("compute"))

        network = EndpointNetworkView.from_dict(d.pop("network"))

        endpoints_view = cls(
            compute=compute,
            network=network,
        )

        return endpoints_view
