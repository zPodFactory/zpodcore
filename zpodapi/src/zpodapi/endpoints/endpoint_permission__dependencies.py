from zpodapi.lib.global_dependencies import service_init_annotation

from .endpoint_permission__services import EndpointPermissionService


class EndpointPermissionDepends:
    pass


class EndpointPermissionAnnotations:
    EndpointPermissionService = service_init_annotation(EndpointPermissionService)
