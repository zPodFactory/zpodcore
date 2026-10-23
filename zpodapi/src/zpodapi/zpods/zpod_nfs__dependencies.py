from zpodapi.lib.global_dependencies import service_init_annotation

from .zpod_nfs__services import ZpodNfsService


class ZpodNfsAnnotations:
    ZpodNfsService = service_init_annotation(ZpodNfsService)
