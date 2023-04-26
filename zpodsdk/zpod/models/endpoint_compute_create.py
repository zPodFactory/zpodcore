from typing import Any, Dict, Type, TypeVar

import attr

T = TypeVar("T", bound="EndpointComputeCreate")


@attr.s(auto_attribs=True)
class EndpointComputeCreate:
    """
    Attributes:
        contentlibrary (str):  Example: my-contentlibrary.
        datacenter (str):  Example: my-datacenter.
        driver (str):  Example: vc.
        hostname (str):  Example: my-vcenter.com.
        name (str):  Example: main.
        password (str):  Example: my-password.
        resource_pool (str):  Example: my-cluster.
        storage_datastore (str):  Example: my-datastore.
        storage_policy (str):  Example: my-storage-policy.
        username (str):  Example: my-username.
        vmfolder (str):  Example: my-vmfolder.
    """

    contentlibrary: str
    datacenter: str
    driver: str
    hostname: str
    name: str
    password: str
    resource_pool: str
    storage_datastore: str
    storage_policy: str
    username: str
    vmfolder: str

    def to_dict(self) -> Dict[str, Any]:
        contentlibrary = self.contentlibrary
        datacenter = self.datacenter
        driver = self.driver
        hostname = self.hostname
        name = self.name
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
                "name": name,
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

        driver = d.pop("driver")

        hostname = d.pop("hostname")

        name = d.pop("name")

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
            name=name,
            password=password,
            resource_pool=resource_pool,
            storage_datastore=storage_datastore,
            storage_policy=storage_policy,
            username=username,
            vmfolder=vmfolder,
        )

        return endpoint_compute_create
