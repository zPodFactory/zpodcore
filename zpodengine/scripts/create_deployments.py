#!/usr/bin/env python
# flake8: noqa
from zpodengine.lib.deployments import create_deployment

create_deployment(flow="component_download")
create_deployment(flow="instance_deploy")
create_deployment(flow="instance_destroy")
create_deployment(flow="instance_component_add")
create_deployment(flow="maintenance_operations")
