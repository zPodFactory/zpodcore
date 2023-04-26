from zpodapi.lib.schema_base import Field, SchemaBase


class D:
    class endpoint:
        id = {"example": 1}
        name = {"example": "mylab"}
        description = {"example": "current testing env"}
        endpoints = {"example": "vcda-4.4.1"}
        enabled = {"example": True}

    class endpoint_compute:
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

    class endpoint_network:
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

    name: str = Field(..., D.endpoint_compute.name)
    driver: str = Field(..., D.endpoint_compute.driver)
    hostname: str = Field(..., D.endpoint_compute.hostname)
    username: str = Field(..., D.endpoint_compute.username)
    datacenter: str = Field(..., D.endpoint_compute.datacenter)
    resource_pool: str = Field(..., D.endpoint_compute.resource_pool)
    storage_policy: str = Field(..., D.endpoint_compute.storage_policy)
    storage_datastore: str = Field(..., D.endpoint_compute.storage_datastore)
    contentlibrary: str = Field(..., D.endpoint_compute.contentlibrary)
    vmfolder: str = Field(..., D.endpoint_compute.vmfolder)


class EndpointNetworkView(SchemaBase):
    class Config:
        extra = "allow"

    name: str = Field(..., D.endpoint_network.name)
    driver: str = Field(..., D.endpoint_network.driver)
    hostname: str = Field(..., D.endpoint_network.hostname)
    username: str = Field(..., D.endpoint_network.username)
    networks: str = Field(..., D.endpoint_network.networks)
    transportzone: str = Field(..., D.endpoint_network.transportzone)
    edgecluster: str = Field(..., D.endpoint_network.edgecluster)
    t0: str = Field(..., D.endpoint_network.t0)
    macdiscoveryprofile: str = Field(..., D.endpoint_network.macdiscoveryprofile)


class EndpointsView(SchemaBase):
    compute: EndpointComputeView
    network: EndpointNetworkView


class EndpointView(SchemaBase):
    id: str = Field(..., D.endpoint.id)
    name: str = Field(..., D.endpoint.name)
    description: str = Field(..., D.endpoint.description)
    enabled: bool = Field(..., D.endpoint.enabled)


class EndpointViewFull(EndpointView):
    endpoints: EndpointsView


class EndpointComputeCreate(SchemaBase):
    name: str = Field(..., D.endpoint_compute.name)
    driver: str = Field(..., D.endpoint_compute.driver)
    hostname: str = Field(..., D.endpoint_compute.hostname)
    username: str = Field(..., D.endpoint_compute.username)
    password: str = Field(..., D.endpoint_compute.password)
    datacenter: str = Field(..., D.endpoint_compute.datacenter)
    resource_pool: str = Field(..., D.endpoint_compute.resource_pool)
    storage_policy: str = Field(..., D.endpoint_compute.storage_policy)
    storage_datastore: str = Field(..., D.endpoint_compute.storage_datastore)
    contentlibrary: str = Field(..., D.endpoint_compute.contentlibrary)
    vmfolder: str = Field(..., D.endpoint_compute.vmfolder)


class EndpointNetworkCreate(SchemaBase):
    name: str = Field(..., D.endpoint_network.name)
    driver: str = Field(..., D.endpoint_network.driver)
    hostname: str = Field(..., D.endpoint_network.hostname)
    username: str = Field(..., D.endpoint_network.username)
    password: str = Field(..., D.endpoint_network.password)
    networks: str = Field(..., D.endpoint_network.networks)
    transportzone: str = Field(..., D.endpoint_network.transportzone)
    edgecluster: str = Field(..., D.endpoint_network.edgecluster)
    t0: str = Field(..., D.endpoint_network.t0)
    macdiscoveryprofile: str = Field(..., D.endpoint_network.macdiscoveryprofile)


class EndpointsCreate(SchemaBase):
    compute: EndpointComputeCreate
    network: EndpointNetworkCreate


class EndpointCreate(SchemaBase):
    name: str = Field(..., D.endpoint.name)
    description: str = Field(..., D.endpoint.description)
    endpoints: EndpointsCreate
    enabled: bool = Field(..., D.endpoint.enabled)


class EndpointComputeUpdate(SchemaBase):
    username: str | None = Field(None, D.endpoint_compute.username)
    password: str | None = Field(None, D.endpoint_compute.password)


class EndpointNetworkUpdate(SchemaBase):
    username: str | None = Field(None, D.endpoint_network.username)
    password: str | None = Field(None, D.endpoint_network.password)


class EndpointsUpdate(SchemaBase):
    compute: None | EndpointComputeUpdate
    network: None | EndpointNetworkUpdate


class EndpointUpdate(SchemaBase):
    description: str | None = Field(None, D.endpoint.description)
    endpoints: EndpointsUpdate = {}
    enabled: bool | None = Field(None, D.endpoint.enabled)
