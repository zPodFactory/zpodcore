from fastapi import APIRouter

from zpodapi.lib.route_logger import RouteLogger

router = APIRouter(
    tags=["root"],
    route_class=RouteLogger,
)


@router.get("/")
async def root():
    return "zPod API"
