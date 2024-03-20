from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.endpoint_compute_create import EndpointComputeCreate
    from ..models.endpoint_network_create import EndpointNetworkCreate


T = TypeVar("T", bound="EndpointsCreate")


@_attrs_define
class EndpointsCreate:
    """
    Attributes:
        compute (EndpointComputeCreate):
        network (EndpointNetworkCreate):
    """

    compute: "EndpointComputeCreate"
    network: "EndpointNetworkCreate"

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
        from ..models.endpoint_compute_create import EndpointComputeCreate
        from ..models.endpoint_network_create import EndpointNetworkCreate

        d = src_dict.copy()
        compute = EndpointComputeCreate.from_dict(d.pop("compute"))

        network = EndpointNetworkCreate.from_dict(d.pop("network"))

        endpoints_create = cls(
            compute=compute,
            network=network,
        )

        return endpoints_create
