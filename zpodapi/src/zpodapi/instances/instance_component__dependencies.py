from zpodapi.lib.global_dependencies import service_init_annotation

from .instance_component__services import InstanceComponentService


class InstanceComponentDepends:
    pass


class InstanceComponentAnnotations:
    InstanceComponentService = service_init_annotation(InstanceComponentService)
