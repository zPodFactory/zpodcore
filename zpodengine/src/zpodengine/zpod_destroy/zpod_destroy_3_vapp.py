from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.vmware import vCenter
from zpodengine import settings
from zpodengine.lib import database


@task
def zpod_destroy_vapp(zpod_id: int):
    print("Delete zPod VAPP")
    with database.get_session_ctx() as session:
        zpod = session.get(M.Zpod, zpod_id)
        with vCenter.auth_by_zpod_endpoint(zpod=zpod) as vc:
            vc.delete_vapp(f"{settings.SITE_ID}-{zpod.name}")
