from functools import partial, wraps

from zpodcommon import models as M
from zpodcommon.enums import InstanceComponentStatus
from zpodengine.lib import database


def set_instance_component_status(
    instance_component_id: int,
    status: InstanceComponentStatus,
):
    with database.get_session_ctx() as session:
        instance_component = session.get(M.InstanceComponent, instance_component_id)
        instance_component.status = status
        session.add(instance_component)
        session.commit()


set_instance_component_status_as_add_failed = partial(
    set_instance_component_status,
    status=InstanceComponentStatus.ADD_FAILED,
)


def handle_instance_component_add_failure(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            set_instance_component_status_as_add_failed(kwargs["instance_component_id"])
            raise

    return wrapper
