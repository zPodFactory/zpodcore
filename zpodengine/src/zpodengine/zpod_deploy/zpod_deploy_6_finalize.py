from prefect import task

from zpodcommon import models as M
from zpodcommon.enums import ZpodStatus
from zpodengine.lib import database


@task
def zpod_deploy_finalize(zpod_id: int):
    with database.get_session_ctx() as session:
        zpod = session.get(M.Zpod, zpod_id)
        zpod.status = ZpodStatus.ACTIVE
        session.add(zpod)
        session.commit()
