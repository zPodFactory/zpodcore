from typing import Any, Dict, Type, TypeVar

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

    def to_dict(self) -> Dict[str, Any]:
        hostname = self.hostname

        ip = self.ip

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "hostname": hostname,
                "ip": ip,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        hostname = d.pop("hostname")

        ip = d.pop("ip")

        zpod_dns_view = cls(
            hostname=hostname,
            ip=ip,
        )

        return zpod_dns_view
