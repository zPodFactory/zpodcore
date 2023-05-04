from prefect import task

from zpodcommon import models as M
from zpodcommon.enums import InstanceStatus
from zpodengine.lib import database


@task
def instance_destroy_finalize(instance_id: int):
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)
        instance.status = InstanceStatus.DELETED
        session.add(instance)
        session.commit()
