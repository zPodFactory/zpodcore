from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.endpoint_network_drivers import EndpointNetworkDrivers

T = TypeVar("T", bound="EndpointNetworkView")


@_attrs_define
class EndpointNetworkView:
    """
    Attributes:
        driver (EndpointNetworkDrivers):
        edgecluster (str):
        hostname (str):
        networks (str):
        t0 (str):
        transportzone (str):
        username (str):
    """

    driver: EndpointNetworkDrivers
    edgecluster: str
    hostname: str
    networks: str
    t0: str
    transportzone: str
    username: str
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        driver = self.driver.value

        edgecluster = self.edgecluster

        hostname = self.hostname

        networks = self.networks

        t0 = self.t0

        transportzone = self.transportzone

        username = self.username

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "driver": driver,
                "edgecluster": edgecluster,
                "hostname": hostname,
                "networks": networks,
                "t0": t0,
                "transportzone": transportzone,
                "username": username,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        driver = EndpointNetworkDrivers(d.pop("driver"))

        edgecluster = d.pop("edgecluster")

        hostname = d.pop("hostname")

        networks = d.pop("networks")

        t0 = d.pop("t0")

        transportzone = d.pop("transportzone")

        username = d.pop("username")

        endpoint_network_view = cls(
            driver=driver,
            edgecluster=edgecluster,
            hostname=hostname,
            networks=networks,
            t0=t0,
            transportzone=transportzone,
            username=username,
        )

        endpoint_network_view.additional_properties = d
        return endpoint_network_view

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
