from prefect import task

from zpodcommon import models as M
from zpodcommon.enums import ZpodStatus
from zpodengine.lib import database
from zpodengine.lib.flow_runs import cancel_zpod_runs


@task
def zpod_destroy_prep(zpod_id: int):
    # A deploy (or any other flow) still running on the zPod would race the destroy:
    # it must be over, and its status writes with it, before DELETING is set.
    with database.get_session_ctx() as session:
        zpod = session.get(M.Zpod, zpod_id)
        reason = f"Cancelled: zPod {zpod.name} is being destroyed"
    cancel_zpod_runs(zpod_id, reason=reason)

    with database.get_session_ctx() as session:
        zpod = session.get(M.Zpod, zpod_id)
        zpod.status = ZpodStatus.DELETING
        session.add(zpod)
        session.commit()
