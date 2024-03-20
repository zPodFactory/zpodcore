from functools import partial, wraps

from zpodcommon import models as M
from zpodcommon.enums import ZpodComponentStatus
from zpodengine.lib import database


def set_zpod_component_status(
    zpod_component_id: int,
    status: ZpodComponentStatus,
):
    with database.get_session_ctx() as session:
        zpod_component = session.get(M.ZpodComponent, zpod_component_id)
        zpod_component.status = status
        session.add(zpod_component)
        session.commit()


set_zpod_component_status_as_add_failed = partial(
    set_zpod_component_status,
    status=ZpodComponentStatus.ADD_FAILED,
)


def handle_zpod_component_add_failure(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            set_zpod_component_status_as_add_failed(kwargs["zpod_component_id"])
            raise

    return wrapper
