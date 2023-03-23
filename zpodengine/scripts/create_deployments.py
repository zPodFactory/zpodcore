#!/usr/bin/env python
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
    flow="component.flow_download_component.flow_download_component",
)

create_deployment(
    flow="instance.flow_deploy_instance.flow_deploy_instance",
)

create_deployment(
    flow="instance_component.flow_add_instance_component.flow_add_instance_component",
)
