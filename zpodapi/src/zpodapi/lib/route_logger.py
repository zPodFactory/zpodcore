from typing import Callable

from fastapi import Request, Response
from fastapi.routing import APIRoute

from zpodapi.lib.panel import log_obj


class RouteLogger(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            req = await request.body()

            url = request.url
            path = f"{url.path}?{url.query}" if url.query else url.path

            log_obj(req, f"REQUEST {path}")
            response: Response = await original_route_handler(request)
            log_obj(response.body, f"RESPONSE {path}")
            return response

        return custom_route_handler
