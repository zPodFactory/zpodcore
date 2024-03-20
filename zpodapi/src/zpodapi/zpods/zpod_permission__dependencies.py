from zpodapi.lib.global_dependencies import service_init_annotation

from .zpod_permission__services import ZpodPermissionService


class ZpodPermissionDepends:
    pass


class ZpodPermissionAnnotations:
    ZpodPermissionService = service_init_annotation(ZpodPermissionService)
