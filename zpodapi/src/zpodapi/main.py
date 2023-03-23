from fastapi import FastAPI
from fastapi.routing import APIRoute

from zpodapi.components import component_routes
from zpodapi.endpoints import endpoint_routes
from zpodapi.instances import (
    instance__routes,
    instance_component__routes,
    instance_feature__routes,
    instance_network__routes,
)
from zpodapi.libraries import library_routes
from zpodapi.root import root_routes
from zpodapi.users import user_routes


def simplify_operation_ids(api: FastAPI) -> None:
    """
    Update operation IDs so that generated API clients have simpler function
    names.
    """
    for route in api.routes:
        if isinstance(route, APIRoute) and not route.operation_id:
            tag = route.tags[0] if route.tags else "default"
            route.operation_id = f"{tag}_{route.name}"


api = FastAPI(title="zPod API")
api.include_router(root_routes.router)
api.include_router(component_routes.router)
api.include_router(endpoint_routes.router)
api.include_router(instance__routes.router)
api.include_router(instance_component__routes.router)
api.include_router(instance_feature__routes.router)
api.include_router(instance_network__routes.router)
api.include_router(library_routes.router)
api.include_router(user_routes.router)

simplify_operation_ids(api)
