#!/usr/bin/env python
from zpodengine.lib.deployments import create_deployment

create_deployment(
    flow="samples.deploy_sample.deploy_sample",
)

create_deployment(
    flow="samples.deploy_sample2.deploy_sample2",
    parameters=dict(zpodname="zpod-default"),
)

create_deployment(
    flow="samples.db_sample.db_sample",
)

create_deployment(
    name="download_component",
    flow="component.download_component.download_component_flow",
)

create_deployment(
    flow="instance.flow_deploy_instance.flow_deploy_instance",
)

create_deployment(
    flow="instance_component.flow_add_instance_component.flow_add_instance_component",
)
