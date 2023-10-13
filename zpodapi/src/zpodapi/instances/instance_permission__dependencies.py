from zpodapi.lib.global_dependencies import service_init_annotation

from .instance_permission__services import InstancePermissionService


class InstancePermissionDepends:
    pass


class InstancePermissionAnnotations:
    InstancePermissionService = service_init_annotation(InstancePermissionService)
