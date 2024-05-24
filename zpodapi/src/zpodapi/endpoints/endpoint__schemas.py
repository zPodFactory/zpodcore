from pydantic import AfterValidator, ConfigDict, StringConstraints
from typing_extensions import Annotated

from zpodapi.lib.schema_base import Field, SchemaBase
from zpodapi.lib.types import validate_fqdn
from zpodcommon import enums


# Annotated[Enum, StringConstraints(to_lower=True)] doesn't work with enum types
def to_lower(value: str):
    return value.lower()


class D:
    id = {"example": 1}
    name = {"example": "mylab"}
    description = {"example": "current testing env"}
    endpoints = {"example": "vcda-4.4.1"}
    status = {"example": "ACTIVE"}

    class compute:
        driver = {"example": "vsphere"}
        hostname = {"example": "my-vcenter.com"}
        username = {"example": "my-username"}
        password = {"example": "my-password"}
        datacenter = {"example": "my-datacenter"}
        resource_pool = {"example": "my-cluster"}
        storage_policy = {"example": "my-storage-policy"}
        storage_datastore = {"example": "my-datastore"}
        contentlibrary = {"example": "my-contentlibrary"}
        vmfolder = {"example": "my-vmfolder"}

    class network:
        driver = {"example": "nsxt"}
        hostname = {"example": "my-nsxt-manager.com"}
        username = {"example": "my-username"}
        password = {"example": "my-password"}
        networks = {"example": "10.196.64.0/18"}
        transportzone = {"example": "my-transportzone"}
        edgecluster = {"example": "my-edgecluster"}
        t0 = {"example": "my-t0"}


class EndpointComputeView(SchemaBase):
    model_config = ConfigDict(extra="ignore")

    driver: enums.EndpointComputeDrivers = Field(..., D.compute.driver)
    hostname: str = Field(..., D.compute.hostname)
    username: str = Field(..., D.compute.username)
    datacenter: str = Field(..., D.compute.datacenter)
    resource_pool: str = Field(..., D.compute.resource_pool)
    storage_policy: str = Field(..., D.compute.storage_policy)
    storage_datastore: str = Field(..., D.compute.storage_datastore)
    contentlibrary: str = Field(..., D.compute.contentlibrary)
    vmfolder: str = Field(..., D.compute.vmfolder)


class EndpointNetworkView(SchemaBase):
    model_config = ConfigDict(extra="ignore")

    driver: enums.EndpointNetworkDrivers = Field(..., D.network.driver)
    hostname: str = Field(..., D.network.hostname)
    username: str = Field(..., D.network.username)
    networks: str = Field(..., D.network.networks)
    transportzone: str = Field(..., D.network.transportzone)
    edgecluster: str = Field(..., D.network.edgecluster)
    t0: str = Field(..., D.network.t0)


class EndpointsView(SchemaBase):
    compute: EndpointComputeView
    network: EndpointNetworkView


class EndpointView(SchemaBase):
    id: int = Field(..., D.id)
    name: str = Field(..., D.name)
    description: str = Field(..., D.description)
    status: enums.EndpointStatus = Field(..., D.status)


class EndpointViewFull(EndpointView):
    endpoints: EndpointsView


class EndpointComputeCreate(SchemaBase):
    driver: Annotated[
        enums.EndpointComputeDrivers,
        AfterValidator(to_lower),
    ] = Field(..., D.compute.driver)
    hostname: Annotated[
        str,
        AfterValidator(validate_fqdn),
    ] = Field(..., D.compute.hostname)
    username: str = Field(..., D.compute.username)
    password: str = Field(..., D.compute.password)
    datacenter: str = Field(..., D.compute.datacenter)
    resource_pool: str = Field(..., D.compute.resource_pool)
    storage_policy: str = Field(..., D.compute.storage_policy)
    storage_datastore: str = Field(..., D.compute.storage_datastore)
    contentlibrary: str = Field(..., D.compute.contentlibrary)
    vmfolder: str = Field(..., D.compute.vmfolder)


class EndpointNetworkCreate(SchemaBase):
    driver: Annotated[
        enums.EndpointNetworkDrivers,
        AfterValidator(to_lower),
    ] = Field(..., D.network.driver)
    hostname: Annotated[
        str,
        AfterValidator(validate_fqdn),
    ] = Field(..., D.network.hostname)
    username: str = Field(..., D.network.username)
    password: str = Field(..., D.network.password)
    networks: str = Field(..., D.network.networks)
    transportzone: str = Field(..., D.network.transportzone)
    edgecluster: str = Field(..., D.network.edgecluster)
    t0: str = Field(..., D.network.t0)


class EndpointsCreate(SchemaBase):
    compute: EndpointComputeCreate
    network: EndpointNetworkCreate


class EndpointCreate(SchemaBase):
    name: Annotated[str, StringConstraints(to_lower=True)] = Field(..., D.name)
    description: str = Field(..., D.description)
    endpoints: EndpointsCreate


class EndpointComputeUpdate(SchemaBase):
    username: str | None = Field(None, D.compute.username)
    password: str | None = Field(None, D.compute.password)


class EndpointNetworkUpdate(SchemaBase):
    username: str | None = Field(None, D.network.username)
    password: str | None = Field(None, D.network.password)


class EndpointsUpdate(SchemaBase):
    compute: None | EndpointComputeUpdate = None
    network: None | EndpointNetworkUpdate = None


class EndpointUpdate(SchemaBase):
    name: Annotated[str, StringConstraints(to_lower=True)] | None = Field(None, D.name)
    description: str | None = Field(None, D.description)
    endpoints: EndpointsUpdate | None = None
