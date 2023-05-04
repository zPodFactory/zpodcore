from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.ovfdeployer import ovf_deployer
from zpodengine.lib import database


@task
def instance_component_add_deploy(keys: dict[str, str | int | None]):
    print("Deploy OVA")
    with database.get_session_ctx() as session:
        instance_component = session.get(M.InstanceComponent, keys)
        ovf_deployer(instance_component)
