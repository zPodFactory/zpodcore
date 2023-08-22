from prefect import task

from zpodcommon import models as M
from zpodcommon.enums import InstanceStatus
from zpodengine.lib import database


@task
def instance_deploy_finalize(instance_id: int):
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)
        instance.status = InstanceStatus.ACTIVE
        session.add(instance)
        session.commit()
