from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="ZpodDnsView")


@_attrs_define
class ZpodDnsView:
    """
    Attributes:
        hostname (str):
        ip (str):
    """

    hostname: str
    ip: str

    def to_dict(self) -> dict[str, Any]:
        hostname = self.hostname

        ip = self.ip

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "hostname": hostname,
                "ip": ip,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        hostname = d.pop("hostname")

        ip = d.pop("ip")

        zpod_dns_view = cls(
            hostname=hostname,
            ip=ip,
        )

        return zpod_dns_view
