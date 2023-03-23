from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="EndpointNetworkCreate")


@attr.s(auto_attribs=True)
class EndpointNetworkCreate:
    """
    Attributes:
        driver (str):  Example: nsxt.
        edgecluster (str):  Example: my-edgecluster.
        hostname (str):  Example: my-nsxt-manager.com.
        name (str):
        password (str):  Example: my-password.
        t0 (str):  Example: my-t0.
        transportzone (str):  Example: my-transportzone.
        username (str):  Example: my-username.
    """

    driver: str
    edgecluster: str
    hostname: str
    name: str
    password: str
    t0: str
    transportzone: str
    username: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        driver = self.driver
        edgecluster = self.edgecluster
        hostname = self.hostname
        name = self.name
        password = self.password
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
                "name": name,
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

        name = d.pop("name")

        password = d.pop("password")

        t0 = d.pop("t0")

        transportzone = d.pop("transportzone")

        username = d.pop("username")

        endpoint_network_create = cls(
            driver=driver,
            edgecluster=edgecluster,
            hostname=hostname,
            name=name,
            password=password,
            t0=t0,
            transportzone=transportzone,
            username=username,
        )

        endpoint_network_create.additional_properties = d
        return endpoint_network_create

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