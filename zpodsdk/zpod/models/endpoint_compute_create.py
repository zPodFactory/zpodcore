from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="EndpointComputeCreate")


@attr.s(auto_attribs=True)
class EndpointComputeCreate:
    """
    Attributes:
        contentlibrary (str):  Example: my-contentlibrary.
        datacenter (str):  Example: my-datacenter.
        driver (str):  Example: current testing env.
        hostname (str):  Example: my-vcenter.com.
        name (str):
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
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

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
        field_dict.update(self.additional_properties)
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

        endpoint_compute_create.additional_properties = d
        return endpoint_compute_create

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