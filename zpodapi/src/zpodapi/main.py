import json
from functools import partial

from fastapi import Depends, FastAPI
from fastapi.routing import APIRoute
from starlette.requests import Request

from zpodapi.lib.panel import log_obj
from zpodapi.root import root_routes
from zpodapi.routers import components, libraries
from zpodapi.users import user_routes


async def log_request(request: Request):
    try:
        out = await request.json()
    except json.JSONDecodeError:
        out = await request.body()
    log_obj(out, f"INCOMING REQUEST {request.method} {request.url.path}")


def simplify_operation_ids(api: FastAPI) -> None:
    """
    Update operation IDs so that generated API clients have simpler function
    names.
    """
    for route in api.routes:
        if isinstance(route, APIRoute):
            tag = route.tags[0] if route.tags else "default"
            route.operation_id = f"{tag}_{route.name}"


api = FastAPI(title="zPod API")
include_router_logged = partial(
    api.include_router,
    dependencies=[Depends(log_request)],
)
include_router_logged(root_routes.router)
include_router_logged(user_routes.router)
include_router_logged(libraries.router)
include_router_logged(components.router)

simplify_operation_ids(api)
