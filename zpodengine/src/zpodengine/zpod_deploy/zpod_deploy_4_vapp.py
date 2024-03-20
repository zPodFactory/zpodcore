from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.vmware import vCenter
from zpodengine import settings
from zpodengine.lib import database


@task
def zpod_deploy_vapp(zpod_id: int):
    print("Create zPod VAPP")
    with database.get_session_ctx() as session:
        zpod = session.get(M.Zpod, zpod_id)
        with vCenter.auth_by_zpod_endpoint(zpod=zpod) as vc:
            # Fetch cluster name & folder name from endpoint.
            rpool_name = zpod.endpoint.endpoints["compute"]["resource_pool"]
            folder_name = zpod.endpoint.endpoints["compute"]["vmfolder"]

            vc.create_vapp(
                f"{settings.SITE_ID}-{zpod.name}",
                rpool_name,
                folder_name,
            )
