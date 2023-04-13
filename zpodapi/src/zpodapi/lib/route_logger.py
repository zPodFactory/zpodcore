from typing import Callable

from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute

from zpodapi.lib.panel import log_obj


class RouteLogger(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            mp = f"{request.method.upper()} {request.url.path}"
            if request.url.query:
                mp += f"?{request.url.query}"

            log_obj(await request.body(), f"REQUEST {mp}")
            try:
                response: Response = await original_route_handler(request)
                log_obj(response.body, f"RESPONSE {mp}")
                return response
            except RequestValidationError as exc:
                log_obj(dict(detail=exc.errors()), f"RESPONSE {mp}")
                raise

        return custom_route_handler
