from enum import Enum


class EndpointComputeDrivers(str, Enum):
    VSPHERE = "vsphere"

    def __str__(self) -> str:
        return str(self.value)
