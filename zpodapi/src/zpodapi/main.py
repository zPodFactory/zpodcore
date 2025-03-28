import traceback

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.routing import APIRoute

from zpodapi import __version__
from zpodapi.components import component__routes
from zpodapi.endpoints import (
    endpoint__routes,
    endpoint_enet__routes,
    endpoint_permission__routes,
)
from zpodapi.lib.global_dependencies import GlobalDepends
from zpodapi.lib.panel import print_panel
from zpodapi.libraries import library__routes
from zpodapi.permission_groups import permission_group__routes
from zpodapi.profiles import profile__routes
from zpodapi.root import root__routes
from zpodapi.settings import setting__routes
from zpodapi.users import user__routes
from zpodapi.zpods import (
    zpod__routes,
    zpod_component__routes,
    zpod_dns__routes,
    zpod_network__routes,
    zpod_permission__routes,
)


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
    dependencies=[
        GlobalDepends.ValidateVersion,
        GlobalDepends.UpdateLastConnectionDate,
    ],
    version=__version__,
)


@api.exception_handler(httpx.RequestError)
async def httpx_request_error_exception_handler(
    request: Request,
    exc: httpx.RequestError,
):
    print_panel(traceback.format_exc(), "HTTPX Error")
    raise HTTPException(
        status_code=418,
        detail=f"An error occurred while requesting url: {exc.request.url}.  {exc}",
    ) from exc


api.include_router(root__routes.router)
api.include_router(component__routes.router)
api.include_router(endpoint__routes.router)
api.include_router(endpoint_enet__routes.router)
api.include_router(endpoint_permission__routes.router)
api.include_router(zpod__routes.router)
api.include_router(zpod_component__routes.router)
api.include_router(zpod_dns__routes.router)
api.include_router(zpod_network__routes.router)
api.include_router(zpod_permission__routes.router)
api.include_router(library__routes.router)
api.include_router(permission_group__routes.router)
api.include_router(profile__routes.router)
api.include_router(setting__routes.router)
api.include_router(user__routes.router)
simplify_operation_ids(api)
