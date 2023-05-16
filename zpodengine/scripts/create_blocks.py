#!/usr/bin/env python

import os

from prefect.infrastructure import DockerContainer

ZPODCORE_PATH = os.environ["ZPODCORE_PATH"]
ZPODCORE_LIBRARY_PATH = os.environ["ZPODCORE_LIBRARY_PATH"]
ZPODCORE_PRODUCTS_PATH = os.environ["ZPODCORE_PRODUCTS_PATH"]
ZPODCORE_DNSMASQ_PATH = os.environ["ZPODCORE_DNSMASQ_PATH"]
ZPODCORE_RESULTS_PATH = os.environ["ZPODCORE_RESULTS_PATH"]
COMPOSE_PROJECT_NAME = os.environ.get("COMPOSE_PROJECT_NAME", "zpodcore")


docker_block = DockerContainer(
    image=f"{COMPOSE_PROJECT_NAME}-zpodengine:v1",
    auto_remove=True,
    volumes=[
        f"{ZPODCORE_PATH}/zpodcommon/src/zpodcommon:/zpodcore/src/zpodcommon",
        f"{ZPODCORE_PATH}/zpodengine/src/zpodengine:/zpodcore/src/zpodengine",
        f"{ZPODCORE_PATH}/.env:/zpodcore/.env",
        f"{ZPODCORE_DNSMASQ_PATH}:/etc/dnsmasq.d",
        f"{ZPODCORE_LIBRARY_PATH}:/library",
        f"{ZPODCORE_PRODUCTS_PATH}:/products",
        f"{ZPODCORE_RESULTS_PATH}:/results",
    ],
    env={
        "PREFECT_API_URL": "http://zpodengineserver:4200/api",
        "PREFECT_LOCAL_STORAGE_PATH": "/results",
    },
    networks=[f"{COMPOSE_PROJECT_NAME}_default"],
)
uuid = docker_block.save("zpodengine", overwrite=True)
print(f"Created Block: zpodengine [{uuid}]")
