from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.zpod_network_view import ZpodNetworkView


T = TypeVar("T", bound="ZpodNetworkRoutingView")


@_attrs_define
class ZpodNetworkRoutingView:
    """
    Attributes:
        network (ZpodNetworkView):
        flow_run_id (None | str | Unset):
    """

    network: ZpodNetworkView
    flow_run_id: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        network = self.network.to_dict()

        flow_run_id: None | str | Unset
        if isinstance(self.flow_run_id, Unset):
            flow_run_id = UNSET
        else:
            flow_run_id = self.flow_run_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "network": network,
            }
        )
        if flow_run_id is not UNSET:
            field_dict["flow_run_id"] = flow_run_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.zpod_network_view import ZpodNetworkView

        d = dict(src_dict)
        network = ZpodNetworkView.from_dict(d.pop("network"))

        def _parse_flow_run_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        flow_run_id = _parse_flow_run_id(d.pop("flow_run_id", UNSET))

        zpod_network_routing_view = cls(
            network=network,
            flow_run_id=flow_run_id,
        )

        return zpod_network_routing_view
