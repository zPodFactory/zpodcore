from prefect import task

from zpodcommon import models as M
from zpodcommon.enums import ZpodNetworkRouting, ZpodStatus
from zpodengine.lib import database


@task
def zpod_destroy_finalize(zpod_id: int):
    with database.get_session_ctx() as session:
        zpod = session.get(M.Zpod, zpod_id)
        zpod.status = ZpodStatus.DELETED
        # The zPod is soft-deleted: its network rows outlive it. The T1 (and its
        # static routes) and zcore (and its masquerade rules) are gone, so no
        # user network may keep looking advertised or masqueraded.
        for network in zpod.user_networks:
            network.routing = ZpodNetworkRouting.LOCAL
            network.masquerade = False
            session.add(network)
        session.add(zpod)
        session.commit()
