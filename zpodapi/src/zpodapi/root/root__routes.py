from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from zpodapi.lib.route_logger import RouteLogger

router = APIRouter(
    tags=["root"],
    route_class=RouteLogger,
)


@router.get("/", response_class=HTMLResponse)
async def root():
    html_content = """
    <html>
        <head>
            <title>zPod API</title>
            <style>
                body {
                    font-family: sans-serif;
                    max-width: 800px;
                    margin: 40px auto;
                    padding: 20px;
                }
                h1 {
                    color: #333;
                }
                a {
                    color: #0066cc;
                    text-decoration: none;
                }
                a:hover {
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <h1>Welcome to zPod API</h1>
            <p>Visit our <a href="/docs">API documentation</a></p>
        </body>
    </html>
    """
    response = HTMLResponse(content=html_content, status_code=200)
    response.headers["X-zPod-API"] = "true"
    return response

