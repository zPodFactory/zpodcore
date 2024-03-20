from zpodapi.lib.global_dependencies import service_init_annotation

from .zpod_feature__services import ZpodFeatureService


class ZpodFeatureDepends:
    pass


class ZpodFeatureAnnotations:
    ZpodFeatureService = service_init_annotation(ZpodFeatureService)
