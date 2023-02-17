#!/usr/bin/env python

import importlib

from prefect.deployments import Deployment
from prefect.infrastructure import DockerContainer


def create_deployment(*, flow: str, **kwargs):
    def get_flow(flow):
        module_name, method = flow.rsplit(".", 1)
        mod = importlib.import_module(f"zpodengine.{module_name}")
        flow_method = getattr(mod, method)
        flow_filepath = getattr(mod, "__file__", None)
        return dict(
            flow=flow_method,
            entrypoint=f"{flow_filepath}:{flow_method.fn.__name__}",
        )

    data = (
        dict(
            apply=True,
            infrastructure=DockerContainer.load("zpodengine"),
            path="/zpodcore/src/zpodengine",
            skip_upload=True,
            version=1,
            work_queue_name="default",
        )
        | (get_flow(flow) if type(flow) == str else dict(flow=flow))
        | kwargs
    )
    result = Deployment.build_from_flow(**data)
    print(f"Created Deployment: {result.name}")
    return result


create_deployment(
    name="deploy_sample",
    flow="samples.deploy_sample.deploy_sample",
)

create_deployment(
    name="deploy_sample2",
    flow="samples.deploy_sample2.deploy_sample2",
    parameters=dict(zpodname="zpod-default"),
)

create_deployment(
    name="db_sample",
    flow="samples.db_sample.db_sample",
)
