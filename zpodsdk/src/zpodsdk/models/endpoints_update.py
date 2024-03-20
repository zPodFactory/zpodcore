from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union, cast

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.endpoint_compute_update import EndpointComputeUpdate
    from ..models.endpoint_network_update import EndpointNetworkUpdate


T = TypeVar("T", bound="EndpointsUpdate")


@_attrs_define
class EndpointsUpdate:
    """
    Attributes:
        compute (Union['EndpointComputeUpdate', None]):
        network (Union['EndpointNetworkUpdate', None]):
    """

    compute: Union["EndpointComputeUpdate", None]
    network: Union["EndpointNetworkUpdate", None]

    def to_dict(self) -> Dict[str, Any]:
        from ..models.endpoint_compute_update import EndpointComputeUpdate
        from ..models.endpoint_network_update import EndpointNetworkUpdate

        compute: Union[Dict[str, Any], None]
        if isinstance(self.compute, EndpointComputeUpdate):
            compute = self.compute.to_dict()
        else:
            compute = self.compute

        network: Union[Dict[str, Any], None]
        if isinstance(self.network, EndpointNetworkUpdate):
            network = self.network.to_dict()
        else:
            network = self.network

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
        from ..models.endpoint_compute_update import EndpointComputeUpdate
        from ..models.endpoint_network_update import EndpointNetworkUpdate

        d = src_dict.copy()

        def _parse_compute(data: object) -> Union["EndpointComputeUpdate", None]:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                compute_type_0 = EndpointComputeUpdate.from_dict(data)

                return compute_type_0
            except:  # noqa: E722
                pass
            return cast(Union["EndpointComputeUpdate", None], data)

        compute = _parse_compute(d.pop("compute"))

        def _parse_network(data: object) -> Union["EndpointNetworkUpdate", None]:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                network_type_0 = EndpointNetworkUpdate.from_dict(data)

                return network_type_0
            except:  # noqa: E722
                pass
            return cast(Union["EndpointNetworkUpdate", None], data)

        network = _parse_network(d.pop("network"))

        endpoints_update = cls(
            compute=compute,
            network=network,
        )

        return endpoints_update
