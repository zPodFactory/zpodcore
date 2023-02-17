#!/usr/bin/env python

import os

from prefect.infrastructure import DockerContainer

ZPODCORE_PATH = os.environ["ZPODCORE_PATH"]
ZPODENGINE_HOSTPORT = os.environ.get("ZPODENGINE_HOSTPORT", "localhost:4200")
COMPOSE_PROJECT_NAME = os.environ.get("COMPOSE_PROJECT_NAME", "zpodcore")


docker_block = DockerContainer(
    image=f"{COMPOSE_PROJECT_NAME}-zpodengine:v1",
    auto_remove=True,
    volumes=[
        f"{ZPODCORE_PATH}/zpodcommon/src/zpodcommon:/zpodcore/src/zpodcommon",
        f"{ZPODCORE_PATH}/zpodengine/src/zpodengine:/zpodcore/src/zpodengine",
        f"{ZPODCORE_PATH}/.env:/zpodcore/.env",
    ],
    env={
        "PREFECT_API_URL": f"http://{ZPODENGINE_HOSTPORT}/api",
    },
)
uuid = docker_block.save("zpodengine", overwrite=True)
print(f"Created Block: zpodengine [{uuid}]")
