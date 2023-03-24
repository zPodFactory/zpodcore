from sqlmodel import SQLModel

from zpodapi.lib.schema_base import Field


class EndpointComputeView(SQLModel):
    name: str = Field(...)
    driver: str = Field(..., example="current testing env")
    hostname: str = Field(..., example="my-vcenter.com")
    username: str = Field(..., example="my-username")
    datacenter: str = Field(..., example="my-datacenter")
    resource_pool: str = Field(..., example="my-cluster")
    storage_policy: str = Field(..., example="my-storage-policy")
    storage_datastore: str = Field(..., example="my-datastore")
    contentlibrary: str = Field(..., example="my-contentlibrary")
    vmfolder: str = Field(..., example="my-vmfolder")


class EndpointNetworkView(SQLModel):
    name: str = Field(...)
    driver: str = Field(..., example="nsxt")
    hostname: str = Field(..., example="my-nsxt-manager.com")
    username: str = Field(..., example="my-username")
    networks: str = Field(..., example="10.196.64.0/18")
    transportzone: str = Field(..., example="my-transportzone")
    edgecluster: str = Field(..., example="my-edgecluster")
    t0: str = Field(..., example="my-t0")


class EndpointsView(SQLModel):
    compute: EndpointComputeView
    network: EndpointNetworkView


class EndpointView(SQLModel):
    name: str = Field(..., example="mylab")
    description: str = Field(..., example="current testing env")
    endpoints: EndpointsView
    enabled: bool = Field(...)


class EndpointComputeCreate(SQLModel):
    name: str = Field(...)
    driver: str = Field(..., example="current testing env")
    hostname: str = Field(..., example="my-vcenter.com")
    username: str = Field(..., example="my-username")
    password: str = Field(..., example="my-password")
    datacenter: str = Field(..., example="my-datacenter")
    resource_pool: str = Field(..., example="my-cluster")
    storage_policy: str = Field(..., example="my-storage-policy")
    storage_datastore: str = Field(..., example="my-datastore")
    contentlibrary: str = Field(..., example="my-contentlibrary")
    vmfolder: str = Field(..., example="my-vmfolder")


class EndpointNetworkCreate(SQLModel):
    name: str = Field(...)
    driver: str = Field(..., example="nsxt")
    hostname: str = Field(..., example="my-nsxt-manager.com")
    username: str = Field(..., example="my-username")
    password: str = Field(..., example="my-password")
    networks: str = Field(..., example="10.196.64.0/18")
    transportzone: str = Field(..., example="my-transportzone")
    edgecluster: str = Field(..., example="my-edgecluster")
    t0: str = Field(..., example="my-t0")


class EndpointsCreate(SQLModel):
    compute: EndpointComputeCreate
    network: EndpointNetworkCreate


class EndpointCreate(SQLModel):
    name: str = Field(..., example="mylab")
    description: str = Field(..., example="current testing env")
    endpoints: EndpointsCreate
    enabled: bool = Field(...)


class EndpointComputeUpdate(SQLModel):
    username: str | None = Field(None, example="my-username")
    password: str | None = Field(None, example="my-password")


class EndpointNetworkUpdate(SQLModel):
    username: str | None = Field(None, example="my-username")
    password: str | None = Field(None, example="my-password")


class EndpointsUpdate(SQLModel):
    compute: None | EndpointComputeUpdate
    network: None | EndpointNetworkUpdate


class EndpointUpdate(SQLModel):
    description: str | None = Field(None, example="current testing env")
    endpoints: EndpointsUpdate
    enabled: bool | None = Field(None, example=True)
