from enum import Enum


class EndpointNetworkDrivers(str, Enum):
    NSXT = "nsxt"
    NSXT_PROJECTS = "nsxt_projects"

    def __str__(self) -> str:
        return str(self.value)
