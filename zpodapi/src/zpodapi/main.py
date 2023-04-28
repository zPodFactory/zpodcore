from fastapi import FastAPI
from fastapi.routing import APIRoute

from zpodapi.components import component__routes
from zpodapi.endpoints import endpoint__routes
from zpodapi.instances import (
    instance__routes,
    instance_component__routes,
    instance_feature__routes,
    instance_network__routes,
)
from zpodapi.lib.global_dependencies import GlobalDepends
from zpodapi.libraries import library__routes
from zpodapi.root import root__routes
from zpodapi.settings import setting__routes
from zpodapi.users import user__routes


def simplify_operation_ids(api: FastAPI) -> None:
    """
    Update operation IDs so that generated API clients have simpler function
    names.
    """
    for route in api.routes:
        if isinstance(route, APIRoute) and not route.operation_id:
            tag = route.tags[0] if route.tags else "default"
            route.operation_id = f"{tag}_{route.name}"


api = FastAPI(
    title="zPod API",
    dependencies=[GlobalDepends.UpdateLastConnectionDate],
)
api.include_router(root__routes.router)
api.include_router(component__routes.router)
api.include_router(endpoint__routes.router)
api.include_router(instance__routes.router)
api.include_router(instance_component__routes.router)
api.include_router(instance_feature__routes.router)
api.include_router(instance_network__routes.router)
api.include_router(library__routes.router)
api.include_router(user__routes.router)
api.include_router(setting__routes.router)

simplify_operation_ids(api)
