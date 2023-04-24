#!/usr/bin/env python
# flake8: noqa
from zpodengine.lib.deployments import create_deployment

create_deployment(
    flow="samples.flow_deploy_sample.flow_deploy_sample",
)

create_deployment(
    flow="samples.flow_deploy_sample2.flow_deploy_sample2",
    parameters=dict(zpodname="zpod-default"),
)

create_deployment(
    flow="samples.flow_db_sample.flow_db_sample",
)

create_deployment(
    flow="component_download.flow_component_download.flow_component_download",
)

create_deployment(
    flow="instance_deploy.flow_instance_deploy.flow_instance_deploy",
)

create_deployment(
    flow="instance_component_add.flow_instance_component_add.flow_instance_component_add",
)
