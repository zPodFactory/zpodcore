from typing import Any, Dict, Type, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ZpodDnsCreate")


@_attrs_define
class ZpodDnsCreate:
    """
    Attributes:
        hostname (str):
        host_id (Union[None, Unset, int]):
        ip (Union[None, Unset, str]):
    """

    hostname: str
    host_id: Union[None, Unset, int] = UNSET
    ip: Union[None, Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        hostname = self.hostname

        host_id: Union[None, Unset, int]
        if isinstance(self.host_id, Unset):
            host_id = UNSET
        else:
            host_id = self.host_id

        ip: Union[None, Unset, str]
        if isinstance(self.ip, Unset):
            ip = UNSET
        else:
            ip = self.ip

        field_dict: Dict[str, Any] = {}
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
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        hostname = d.pop("hostname")

        def _parse_host_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        host_id = _parse_host_id(d.pop("host_id", UNSET))

        def _parse_ip(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        ip = _parse_ip(d.pop("ip", UNSET))

        zpod_dns_create = cls(
            hostname=hostname,
            host_id=host_id,
            ip=ip,
        )

        return zpod_dns_create
