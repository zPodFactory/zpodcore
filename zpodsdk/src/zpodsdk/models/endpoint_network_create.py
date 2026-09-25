from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.endpoint_network_drivers import EndpointNetworkDrivers

T = TypeVar("T", bound="EndpointNetworkCreate")


@_attrs_define
class EndpointNetworkCreate:
    """
    Attributes:
        driver (EndpointNetworkDrivers):
        edgecluster (str):
        hostname (str):
        networks (str):
        password (str):
        t0 (str):
        transportzone (str):
        username (str):
    """

    driver: EndpointNetworkDrivers
    edgecluster: str
    hostname: str
    networks: str
    password: str
    t0: str
    transportzone: str
    username: str

    def to_dict(self) -> dict[str, Any]:
        driver = self.driver.value

        edgecluster = self.edgecluster

        hostname = self.hostname

        networks = self.networks

        password = self.password

        t0 = self.t0

        transportzone = self.transportzone

        username = self.username

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "driver": driver,
                "edgecluster": edgecluster,
                "hostname": hostname,
                "networks": networks,
                "password": password,
                "t0": t0,
                "transportzone": transportzone,
                "username": username,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        driver = EndpointNetworkDrivers(d.pop("driver"))

        edgecluster = d.pop("edgecluster")

        hostname = d.pop("hostname")

        networks = d.pop("networks")

        password = d.pop("password")

        t0 = d.pop("t0")

        transportzone = d.pop("transportzone")

        username = d.pop("username")

        endpoint_network_create = cls(
            driver=driver,
            edgecluster=edgecluster,
            hostname=hostname,
            networks=networks,
            password=password,
            t0=t0,
            transportzone=transportzone,
            username=username,
        )

        return endpoint_network_create
