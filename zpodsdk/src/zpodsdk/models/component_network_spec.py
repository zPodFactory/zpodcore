from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ComponentNetworkSpec")


@_attrs_define
class ComponentNetworkSpec:
    """
    Attributes:
        dns (None | str | Unset): Default: zcore.
        gateway (None | str | Unset): Default: the gateway of the zPod network holding the IP.
        ip (None | str | Unset): Address with its prefix, for a subnet the portgroup's VLAN can't give (an isolated
            lab). Default: host_id on the network the portgroup carries.
        portgroup (None | str | Unset): An existing portgroup of the zPod's vCenter, by name or inventory path; every
            NIC goes on it. Its VLAN picks the zPod network the address comes from. Default: VM Network.
    """

    dns: None | str | Unset = UNSET
    gateway: None | str | Unset = UNSET
    ip: None | str | Unset = UNSET
    portgroup: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        dns: None | str | Unset
        if isinstance(self.dns, Unset):
            dns = UNSET
        else:
            dns = self.dns

        gateway: None | str | Unset
        if isinstance(self.gateway, Unset):
            gateway = UNSET
        else:
            gateway = self.gateway

        ip: None | str | Unset
        if isinstance(self.ip, Unset):
            ip = UNSET
        else:
            ip = self.ip

        portgroup: None | str | Unset
        if isinstance(self.portgroup, Unset):
            portgroup = UNSET
        else:
            portgroup = self.portgroup

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if dns is not UNSET:
            field_dict["dns"] = dns
        if gateway is not UNSET:
            field_dict["gateway"] = gateway
        if ip is not UNSET:
            field_dict["ip"] = ip
        if portgroup is not UNSET:
            field_dict["portgroup"] = portgroup

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_dns(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        dns = _parse_dns(d.pop("dns", UNSET))

        def _parse_gateway(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        gateway = _parse_gateway(d.pop("gateway", UNSET))

        def _parse_ip(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        ip = _parse_ip(d.pop("ip", UNSET))

        def _parse_portgroup(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        portgroup = _parse_portgroup(d.pop("portgroup", UNSET))

        component_network_spec = cls(
            dns=dns,
            gateway=gateway,
            ip=ip,
            portgroup=portgroup,
        )

        return component_network_spec
