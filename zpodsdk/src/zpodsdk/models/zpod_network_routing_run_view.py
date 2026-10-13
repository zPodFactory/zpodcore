from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.zpod_network_view import ZpodNetworkView


T = TypeVar("T", bound="ZpodNetworkRoutingRunView")


@_attrs_define
class ZpodNetworkRoutingRunView:
    """A routing flow run as zpodengine reports it, with the network as it is now.

    Attributes:
        flow_run_id (str):
        network (ZpodNetworkView):
        state (str):
        message (None | str | Unset):
        name (None | str | Unset):
    """

    flow_run_id: str
    network: ZpodNetworkView
    state: str
    message: None | str | Unset = UNSET
    name: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        flow_run_id = self.flow_run_id

        network = self.network.to_dict()

        state = self.state

        message: None | str | Unset
        if isinstance(self.message, Unset):
            message = UNSET
        else:
            message = self.message

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "flow_run_id": flow_run_id,
                "network": network,
                "state": state,
            }
        )
        if message is not UNSET:
            field_dict["message"] = message
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.zpod_network_view import ZpodNetworkView

        d = dict(src_dict)
        flow_run_id = d.pop("flow_run_id")

        network = ZpodNetworkView.from_dict(d.pop("network"))

        state = d.pop("state")

        def _parse_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        message = _parse_message(d.pop("message", UNSET))

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        zpod_network_routing_run_view = cls(
            flow_run_id=flow_run_id,
            network=network,
            state=state,
            message=message,
            name=name,
        )

        return zpod_network_routing_run_view
