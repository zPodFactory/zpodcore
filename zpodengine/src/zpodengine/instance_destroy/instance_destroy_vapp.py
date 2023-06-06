from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.vmware import vCenter
from zpodengine import settings
from zpodengine.lib import database


@task
def instance_destroy_vapp(instance_id: int):
    print("Delete Instance VAPP")
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)
        with vCenter.auth_by_instance(instance=instance) as vc:
            vc.delete_vapp(f"{settings.SITE_ID}-{instance.name}")
