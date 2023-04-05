from zpodapi.lib.global_dependencies import service_init_annotation

from .instance_network__services import InstanceNetworkService


class InstanceNetworkDepends:
    pass


class InstanceNetworkAnnotations:
    InstanceNetworkService = service_init_annotation(InstanceNetworkService)
