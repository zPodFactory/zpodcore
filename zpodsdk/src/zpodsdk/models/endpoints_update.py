from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.endpoint_compute_update import EndpointComputeUpdate
    from ..models.endpoint_network_update import EndpointNetworkUpdate


T = TypeVar("T", bound="EndpointsUpdate")


@_attrs_define
class EndpointsUpdate:
    """
    Attributes:
        compute (EndpointComputeUpdate | None | Unset):
        network (EndpointNetworkUpdate | None | Unset):
    """

    compute: EndpointComputeUpdate | None | Unset = UNSET
    network: EndpointNetworkUpdate | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.endpoint_compute_update import EndpointComputeUpdate
        from ..models.endpoint_network_update import EndpointNetworkUpdate

        compute: dict[str, Any] | None | Unset
        if isinstance(self.compute, Unset):
            compute = UNSET
        elif isinstance(self.compute, EndpointComputeUpdate):
            compute = self.compute.to_dict()
        else:
            compute = self.compute

        network: dict[str, Any] | None | Unset
        if isinstance(self.network, Unset):
            network = UNSET
        elif isinstance(self.network, EndpointNetworkUpdate):
            network = self.network.to_dict()
        else:
            network = self.network

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if compute is not UNSET:
            field_dict["compute"] = compute
        if network is not UNSET:
            field_dict["network"] = network

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.endpoint_compute_update import EndpointComputeUpdate
        from ..models.endpoint_network_update import EndpointNetworkUpdate

        d = dict(src_dict)

        def _parse_compute(data: object) -> EndpointComputeUpdate | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                compute_type_0 = EndpointComputeUpdate.from_dict(data)

                return compute_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(EndpointComputeUpdate | None | Unset, data)

        compute = _parse_compute(d.pop("compute", UNSET))

        def _parse_network(data: object) -> EndpointNetworkUpdate | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                network_type_0 = EndpointNetworkUpdate.from_dict(data)

                return network_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(EndpointNetworkUpdate | None | Unset, data)

        network = _parse_network(d.pop("network", UNSET))

        endpoints_update = cls(
            compute=compute,
            network=network,
        )

        return endpoints_update
