from typing import Any, Dict, Type, TypeVar

import attr

T = TypeVar("T", bound="EndpointNetworkCreate")


@attr.s(auto_attribs=True)
class EndpointNetworkCreate:
    """
    Attributes:
        driver (str):  Example: nsxt.
        edgecluster (str):  Example: my-edgecluster.
        hostname (str):  Example: my-nsxt-manager.com.
        macdiscoveryprofile (str):  Example: my-macdiscoveryprofile.
        name (str):  Example: main.
        networks (str):  Example: 10.196.64.0/18.
        password (str):  Example: my-password.
        t0 (str):  Example: my-t0.
        transportzone (str):  Example: my-transportzone.
        username (str):  Example: my-username.
    """

    driver: str
    edgecluster: str
    hostname: str
    macdiscoveryprofile: str
    name: str
    networks: str
    password: str
    t0: str
    transportzone: str
    username: str

    def to_dict(self) -> Dict[str, Any]:
        driver = self.driver
        edgecluster = self.edgecluster
        hostname = self.hostname
        macdiscoveryprofile = self.macdiscoveryprofile
        name = self.name
        networks = self.networks
        password = self.password
        t0 = self.t0
        transportzone = self.transportzone
        username = self.username

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "driver": driver,
                "edgecluster": edgecluster,
                "hostname": hostname,
                "macdiscoveryprofile": macdiscoveryprofile,
                "name": name,
                "networks": networks,
                "password": password,
                "t0": t0,
                "transportzone": transportzone,
                "username": username,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        driver = d.pop("driver")

        edgecluster = d.pop("edgecluster")

        hostname = d.pop("hostname")

        macdiscoveryprofile = d.pop("macdiscoveryprofile")

        name = d.pop("name")

        networks = d.pop("networks")

        password = d.pop("password")

        t0 = d.pop("t0")

        transportzone = d.pop("transportzone")

        username = d.pop("username")

        endpoint_network_create = cls(
            driver=driver,
            edgecluster=edgecluster,
            hostname=hostname,
            macdiscoveryprofile=macdiscoveryprofile,
            name=name,
            networks=networks,
            password=password,
            t0=t0,
            transportzone=transportzone,
            username=username,
        )

        return endpoint_network_create
