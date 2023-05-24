from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.ovfdeployer import ovf_deployer
from zpodengine.instance_component_add.instance_component_add_utils import (
    handle_instance_component_add_failure,
)
from zpodengine.lib import database


@task
@handle_instance_component_add_failure
def instance_component_add_deploy(*, instance_component_id: int):
    print("Deploy OVA")
    with database.get_session_ctx() as session:
        instance_component = session.get(M.InstanceComponent, instance_component_id)
        ovf_deployer(instance_component)
