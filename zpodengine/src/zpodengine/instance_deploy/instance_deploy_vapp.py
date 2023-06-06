from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.vmware import vCenter
from zpodengine import settings
from zpodengine.lib import database


@task
def instance_deploy_vapp(instance_id: int):
    print("Create Instance VAPP")
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)
        with vCenter.auth_by_instance(instance=instance) as vc:
            # Fetch cluster name & folder name from endpoint.
            rpool_name = instance.endpoint.endpoints["compute"]["resource_pool"]
            folder_name = instance.endpoint.endpoints["compute"]["vmfolder"]

            vc.create_vapp(
                f"{settings.SITE_ID}-{instance.name}",
                rpool_name,
                folder_name,
            )
