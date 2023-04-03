from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.endpoint_compute_update import EndpointComputeUpdate
    from ..models.endpoint_network_update import EndpointNetworkUpdate


T = TypeVar("T", bound="EndpointsUpdate")


@attr.s(auto_attribs=True)
class EndpointsUpdate:
    """
    Attributes:
        compute (Union[Unset, EndpointComputeUpdate]):
        network (Union[Unset, EndpointNetworkUpdate]):
    """

    compute: Union[Unset, "EndpointComputeUpdate"] = UNSET
    network: Union[Unset, "EndpointNetworkUpdate"] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        compute: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.compute, Unset):
            compute = self.compute.to_dict()

        network: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.network, Unset):
            network = self.network.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if compute is not UNSET:
            field_dict["compute"] = compute
        if network is not UNSET:
            field_dict["network"] = network

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.endpoint_compute_update import EndpointComputeUpdate
        from ..models.endpoint_network_update import EndpointNetworkUpdate

        d = src_dict.copy()
        _compute = d.pop("compute", UNSET)
        compute: Union[Unset, EndpointComputeUpdate]
        if isinstance(_compute, Unset):
            compute = UNSET
        else:
            compute = EndpointComputeUpdate.from_dict(_compute)

        _network = d.pop("network", UNSET)
        network: Union[Unset, EndpointNetworkUpdate]
        if isinstance(_network, Unset):
            network = UNSET
        else:
            network = EndpointNetworkUpdate.from_dict(_network)

        endpoints_update = cls(
            compute=compute,
            network=network,
        )

        return endpoints_update
