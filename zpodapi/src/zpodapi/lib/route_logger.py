from collections.abc import Callable

from fastapi import HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute

from zpodapi.lib.panel import log_obj
from zpodcommon.lib.debug_level import debug_enabled


class RouteLogger(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            # At INFO level skip the dump entirely (the uvicorn access log is
            # the INFO baseline) — and avoid reading the request body at all.
            if not debug_enabled():
                return await original_route_handler(request)

            mp = f"{request.method.upper()} {request.url.path}"
            if request.url.query:
                mp += f"?{request.url.query}"

            if body := await request.body():
                log_obj(body, f"REQUEST {mp}")
            try:
                response: Response = await original_route_handler(request)
                if response.body:
                    log_obj(response.body, f"RESPONSE {mp}")
                return response
            except RequestValidationError as exc:
                log_obj({"detail": exc.errors()}, f"RESPONSE {mp}")
                raise
            except HTTPException as exc:
                log_obj({"detail": exc.detail}, f"RESPONSE {mp}")
                raise

        return custom_route_handler
