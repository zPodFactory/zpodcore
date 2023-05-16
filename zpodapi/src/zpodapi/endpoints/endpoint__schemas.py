from zpodapi.lib.schema_base import Field, SchemaBase


class D:
    id = {"example": 1}
    name = {"example": "mylab"}
    description = {"example": "current testing env"}
    endpoints = {"example": "vcda-4.4.1"}
    enabled = {"example": True}

    class compute:
        name = {"example": "main"}
        driver = {"example": "vc"}
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
        name = {"example": "main"}
        driver = {"example": "nsxt"}
        hostname = {"example": "my-nsxt-manager.com"}
        username = {"example": "my-username"}
        password = {"example": "my-password"}
        networks = {"example": "10.196.64.0/18"}
        transportzone = {"example": "my-transportzone"}
        edgecluster = {"example": "my-edgecluster"}
        t0 = {"example": "my-t0"}
        macdiscoveryprofile = {"example": "my-macdiscoveryprofile"}


class EndpointComputeView(SchemaBase):
    class Config:
        extra = "allow"

    name: str = Field(..., D.compute.name)
    driver: str = Field(..., D.compute.driver)
    hostname: str = Field(..., D.compute.hostname)
    username: str = Field(..., D.compute.username)
    datacenter: str = Field(..., D.compute.datacenter)
    resource_pool: str = Field(..., D.compute.resource_pool)
    storage_policy: str = Field(..., D.compute.storage_policy)
    storage_datastore: str = Field(..., D.compute.storage_datastore)
    contentlibrary: str = Field(..., D.compute.contentlibrary)
    vmfolder: str = Field(..., D.compute.vmfolder)


class EndpointNetworkView(SchemaBase):
    class Config:
        extra = "allow"

    name: str = Field(..., D.network.name)
    driver: str = Field(..., D.network.driver)
    hostname: str = Field(..., D.network.hostname)
    username: str = Field(..., D.network.username)
    networks: str = Field(..., D.network.networks)
    transportzone: str = Field(..., D.network.transportzone)
    edgecluster: str = Field(..., D.network.edgecluster)
    t0: str = Field(..., D.network.t0)
    macdiscoveryprofile: str = Field(..., D.network.macdiscoveryprofile)


class EndpointsView(SchemaBase):
    compute: EndpointComputeView
    network: EndpointNetworkView


class EndpointView(SchemaBase):
    id: str = Field(..., D.id)
    name: str = Field(..., D.name)
    description: str = Field(..., D.description)
    enabled: bool = Field(..., D.enabled)


class EndpointViewFull(EndpointView):
    endpoints: EndpointsView


class EndpointComputeCreate(SchemaBase):
    name: str = Field(..., D.compute.name)
    driver: str = Field(..., D.compute.driver)
    hostname: str = Field(..., D.compute.hostname)
    username: str = Field(..., D.compute.username)
    password: str = Field(..., D.compute.password)
    datacenter: str = Field(..., D.compute.datacenter)
    resource_pool: str = Field(..., D.compute.resource_pool)
    storage_policy: str = Field(..., D.compute.storage_policy)
    storage_datastore: str = Field(..., D.compute.storage_datastore)
    contentlibrary: str = Field(..., D.compute.contentlibrary)
    vmfolder: str = Field(..., D.compute.vmfolder)


class EndpointNetworkCreate(SchemaBase):
    name: str = Field(..., D.network.name)
    driver: str = Field(..., D.network.driver)
    hostname: str = Field(..., D.network.hostname)
    username: str = Field(..., D.network.username)
    password: str = Field(..., D.network.password)
    networks: str = Field(..., D.network.networks)
    transportzone: str = Field(..., D.network.transportzone)
    edgecluster: str = Field(..., D.network.edgecluster)
    t0: str = Field(..., D.network.t0)
    macdiscoveryprofile: str = Field(..., D.network.macdiscoveryprofile)


class EndpointsCreate(SchemaBase):
    compute: EndpointComputeCreate
    network: EndpointNetworkCreate


class EndpointCreate(SchemaBase):
    name: str = Field(..., D.name)
    description: str = Field(..., D.description)
    endpoints: EndpointsCreate
    enabled: bool = Field(..., D.enabled)


class EndpointComputeUpdate(SchemaBase):
    username: str | None = Field(None, D.compute.username)
    password: str | None = Field(None, D.compute.password)


class EndpointNetworkUpdate(SchemaBase):
    username: str | None = Field(None, D.network.username)
    password: str | None = Field(None, D.network.password)


class EndpointsUpdate(SchemaBase):
    compute: None | EndpointComputeUpdate
    network: None | EndpointNetworkUpdate


class EndpointUpdate(SchemaBase):
    description: str | None = Field(None, D.description)
    endpoints: EndpointsUpdate = {}
    enabled: bool | None = Field(None, D.enabled)
