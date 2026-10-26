from zpodapi.lib.global_dependencies import service_init_annotation

from .zpod_disk__services import ZpodDiskService


class ZpodDiskAnnotations:
    ZpodDiskService = service_init_annotation(ZpodDiskService)
