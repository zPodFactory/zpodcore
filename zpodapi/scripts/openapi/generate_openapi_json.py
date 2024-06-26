import json

from fastapi.openapi.utils import get_openapi

from zpodapi.main import api


def generate_openapi_json():
    with open("/zpodcore/scripts/openapi/openapi.json", "w") as f:
        json.dump(
            get_openapi(
                title=api.title,
                version=api.version,
                openapi_version=api.openapi_version,
                description=api.description,
                routes=api.routes,
            ),
            f,
            indent=2,
            sort_keys=True,
        )


if "main" in __name__:
    print("Generating openapi.json...")
    generate_openapi_json()
