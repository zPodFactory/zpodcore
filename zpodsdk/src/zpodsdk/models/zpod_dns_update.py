from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ZpodDnsUpdate")


@_attrs_define
class ZpodDnsUpdate:
    """
    Attributes:
        hostname (str):
        host_id (int | None | Unset):
        ip (None | str | Unset):
    """

    hostname: str
    host_id: int | None | Unset = UNSET
    ip: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        hostname = self.hostname

        host_id: int | None | Unset
        if isinstance(self.host_id, Unset):
            host_id = UNSET
        else:
            host_id = self.host_id

        ip: None | str | Unset
        if isinstance(self.ip, Unset):
            ip = UNSET
        else:
            ip = self.ip

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "hostname": hostname,
            }
        )
        if host_id is not UNSET:
            field_dict["host_id"] = host_id
        if ip is not UNSET:
            field_dict["ip"] = ip

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        hostname = d.pop("hostname")

        def _parse_host_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        host_id = _parse_host_id(d.pop("host_id", UNSET))

        def _parse_ip(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        ip = _parse_ip(d.pop("ip", UNSET))

        zpod_dns_update = cls(
            hostname=hostname,
            host_id=host_id,
            ip=ip,
        )

        return zpod_dns_update
