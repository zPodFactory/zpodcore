#!/usr/bin/env python
# flake8: noqa
from zpodengine.lib.deployments import create_deployment

create_deployment(
    flow="component_download.flow_component_download.flow_component_download",
)

create_deployment(
    flow="instance_deploy.flow_instance_deploy.flow_instance_deploy",
)

create_deployment(
    flow="instance_component_add.flow_instance_component_add.flow_instance_component_add",
)
