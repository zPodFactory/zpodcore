from typing import Any, Dict, Type, TypeVar

from attrs import define as _attrs_define

from ..models.endpoint_compute_drivers import EndpointComputeDrivers

T = TypeVar("T", bound="EndpointComputeCreate")


@_attrs_define
class EndpointComputeCreate:
    """
    Attributes:
        contentlibrary (str):
        datacenter (str):
        driver (EndpointComputeDrivers):
        hostname (str):
        password (str):
        resource_pool (str):
        storage_datastore (str):
        storage_policy (str):
        username (str):
        vmfolder (str):
    """

    contentlibrary: str
    datacenter: str
    driver: EndpointComputeDrivers
    hostname: str
    password: str
    resource_pool: str
    storage_datastore: str
    storage_policy: str
    username: str
    vmfolder: str

    def to_dict(self) -> Dict[str, Any]:
        contentlibrary = self.contentlibrary

        datacenter = self.datacenter

        driver = self.driver.value

        hostname = self.hostname

        password = self.password

        resource_pool = self.resource_pool

        storage_datastore = self.storage_datastore

        storage_policy = self.storage_policy

        username = self.username

        vmfolder = self.vmfolder

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "contentlibrary": contentlibrary,
                "datacenter": datacenter,
                "driver": driver,
                "hostname": hostname,
                "password": password,
                "resource_pool": resource_pool,
                "storage_datastore": storage_datastore,
                "storage_policy": storage_policy,
                "username": username,
                "vmfolder": vmfolder,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        contentlibrary = d.pop("contentlibrary")

        datacenter = d.pop("datacenter")

        driver = EndpointComputeDrivers(d.pop("driver"))

        hostname = d.pop("hostname")

        password = d.pop("password")

        resource_pool = d.pop("resource_pool")

        storage_datastore = d.pop("storage_datastore")

        storage_policy = d.pop("storage_policy")

        username = d.pop("username")

        vmfolder = d.pop("vmfolder")

        endpoint_compute_create = cls(
            contentlibrary=contentlibrary,
            datacenter=datacenter,
            driver=driver,
            hostname=hostname,
            password=password,
            resource_pool=resource_pool,
            storage_datastore=storage_datastore,
            storage_policy=storage_policy,
            username=username,
            vmfolder=vmfolder,
        )

        return endpoint_compute_create
