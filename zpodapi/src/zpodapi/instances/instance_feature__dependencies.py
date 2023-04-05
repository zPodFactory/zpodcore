from zpodapi.lib.global_dependencies import service_init_annotation

from .instance_feature__services import InstanceFeatureService


class InstanceFeatureDepends:
    pass


class InstanceFeatureAnnotations:
    InstanceFeatureService = service_init_annotation(InstanceFeatureService)
