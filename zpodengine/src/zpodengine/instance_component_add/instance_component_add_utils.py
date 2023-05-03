from zpodcommon import models as M
from zpodcommon.enums import InstanceComponentStatus
from zpodengine.lib import database


def set_instance_component_status(keys, status):
    with database.get_session_ctx() as session:
        instance_component = session.get(M.InstanceComponent, keys)
        instance_component.status = status
        session.add(instance_component)
        session.commit()


def instance_component_add_failed(keys):
    def mark_instance_component_as_failed(task, task_run, state):
        return set_instance_component_status(keys, InstanceComponentStatus.ADD_FAILED)

    return mark_instance_component_as_failed
