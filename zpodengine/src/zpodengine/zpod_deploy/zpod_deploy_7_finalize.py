from prefect import task

from zpodcommon import models as M
from zpodcommon.enums import ZpodStatus
from zpodengine.lib import database
from zpodengine.lib.zpod_status import set_zpod_status


@task
def zpod_deploy_finalize(zpod_id: int):
    with database.get_session_ctx() as session:
        zpod = session.get(M.Zpod, zpod_id)
        set_zpod_status(zpod, ZpodStatus.ACTIVE)
        session.add(zpod)
        session.commit()
