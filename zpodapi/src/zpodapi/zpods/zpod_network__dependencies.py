from zpodapi.lib.global_dependencies import service_init_annotation

from .zpod_network__services import ZpodNetworkService


class ZpodNetworkDepends:
    pass


class ZpodNetworkAnnotations:
    ZPodNetworkService = service_init_annotation(ZpodNetworkService)
