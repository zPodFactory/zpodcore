"""Smoke tests for zpodengine pure helpers.

Prefect flows themselves require a live Prefect runtime, so we don't exercise
them here. We just verify the supporting helper modules import cleanly.
"""


def test_import_lib_modules():
    from zpodengine.lib import network, options, utils  # noqa: F401


def test_import_flow_modules():
    from zpodengine.component_download import flow_component_download  # noqa: F401
    from zpodengine.zpod_deploy import flow_zpod_deploy  # noqa: F401
    from zpodengine.zpod_destroy import flow_zpod_destroy  # noqa: F401


def test_import_prefect_docker():
    # `just zpodengine-deploy-all` runs prefect.yaml's build_docker_image step
    # through prefect_docker, which pulls in prefect.workers.base. A lock
    # refresh once dropped a transitive module that import needs
    # (importlib_metadata), and only deploy-all noticed. Keep it covered here.
    from prefect_docker.deployments import steps  # noqa: F401
    from prefect_docker.worker import DockerWorker  # noqa: F401
