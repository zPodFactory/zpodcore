from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.endpoint_compute_drivers import EndpointComputeDrivers
from ..types import UNSET, Unset

T = TypeVar("T", bound="EndpointComputeView")


@_attrs_define
class EndpointComputeView:
    """
    Attributes:
        contentlibrary (str):
        datacenter (str):
        driver (EndpointComputeDrivers):
        hostname (str):
        resource_pool (str):
        storage_datastore (str):
        storage_policy (str):
        username (str):
        vmfolder (str):
        vds (Union[Unset, str]):  Default: ''.
    """

    contentlibrary: str
    datacenter: str
    driver: EndpointComputeDrivers
    hostname: str
    resource_pool: str
    storage_datastore: str
    storage_policy: str
    username: str
    vmfolder: str
    vds: Union[Unset, str] = ""
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        contentlibrary = self.contentlibrary

        datacenter = self.datacenter

        driver = self.driver.value

        hostname = self.hostname

        resource_pool = self.resource_pool

        storage_datastore = self.storage_datastore

        storage_policy = self.storage_policy

        username = self.username

        vmfolder = self.vmfolder

        vds = self.vds

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "contentlibrary": contentlibrary,
                "datacenter": datacenter,
                "driver": driver,
                "hostname": hostname,
                "resource_pool": resource_pool,
                "storage_datastore": storage_datastore,
                "storage_policy": storage_policy,
                "username": username,
                "vmfolder": vmfolder,
            }
        )
        if vds is not UNSET:
            field_dict["vds"] = vds

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        contentlibrary = d.pop("contentlibrary")

        datacenter = d.pop("datacenter")

        driver = EndpointComputeDrivers(d.pop("driver"))

        hostname = d.pop("hostname")

        resource_pool = d.pop("resource_pool")

        storage_datastore = d.pop("storage_datastore")

        storage_policy = d.pop("storage_policy")

        username = d.pop("username")

        vmfolder = d.pop("vmfolder")

        vds = d.pop("vds", UNSET)

        endpoint_compute_view = cls(
            contentlibrary=contentlibrary,
            datacenter=datacenter,
            driver=driver,
            hostname=hostname,
            resource_pool=resource_pool,
            storage_datastore=storage_datastore,
            storage_policy=storage_policy,
            username=username,
            vmfolder=vmfolder,
            vds=vds,
        )

        endpoint_compute_view.additional_properties = d
        return endpoint_compute_view

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
