from zpodapi.lib.global_dependencies import service_init_annotation

from .zpod_storage__services import ZpodStorageService


class ZpodStorageAnnotations:
    ZpodStorageService = service_init_annotation(ZpodStorageService)
