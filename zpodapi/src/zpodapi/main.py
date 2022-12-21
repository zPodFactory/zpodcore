import json
from functools import partial

from fastapi import Depends, FastAPI
from fastapi.routing import APIRoute
from starlette.requests import Request

from zpodapi.lib.panel import log_obj
from zpodapi.routers import root, users


async def log_request(request: Request):
    try:
        out = await request.json()
    except json.JSONDecodeError:
        out = await request.body()
    log_obj(out, f"INCOMING REQUEST {request.method} {request.url.path}")


def use_route_names_as_operation_ids(api: FastAPI) -> None:
    """
    Simplify operation IDs so that generated API clients have simpler function
    names.
    """
    for route in api.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name


api = FastAPI(title="zPod API")
include_router_logged = partial(
    api.include_router,
    dependencies=[Depends(log_request)],
)
include_router_logged(root.router)
include_router_logged(users.router)

use_route_names_as_operation_ids(api)
