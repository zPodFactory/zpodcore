import json

from prefect import flow, task

from zpodcommon import models as M
from zpodcommon.lib.vmware import vCenter
from zpodengine import settings
from zpodengine.lib import database
from zpodengine.lib.utils import ctx_param


def set_flow_name():
    with database.get_session_ctx() as session:
        instance_component = session.get(
            M.InstanceComponent,
            ctx_param("instance_component_id"),
        )
        return (
            f"Remove Instance Component {instance_component.instance.name} "
            f"{instance_component.hostname}"
        )


@flow(
    name="instance_component_remove",
    flow_run_name=set_flow_name,
    log_prints=True,
)
def flow_instance_component_remove(
    instance_component_id: int,
):
    vc = remove_from_vcenter.submit(instance_component_id)
    remove_from_db.submit(instance_component_id, wait_for=[vc])


@task()
def remove_from_vcenter(instance_component_id: int):
    with database.get_session_ctx() as session:
        instance_component = session.get(M.InstanceComponent, instance_component_id)

        # Open Component JSON file
        f = open(instance_component.component.jsonfile)

        # Load component JSON
        cjson = json.load(f)

        instance = instance_component.instance
        if cjson["component_isnested"]:
            with vCenter.auth_by_instance(instance=instance) as vc:
                vc.delete_vm_nested(
                    domain_name=instance.domain,
                    vm_name=instance_component.hostname,
                )
        else:
            with vCenter.auth_by_instance_endpoint(instance=instance) as vc:
                vc.delete_vm_from_vapp(
                    vapp_name=f"{settings.SITE_ID}-{instance.name}",
                    vm_name=instance_component.fqdn,
                )


@task()
def remove_from_db(instance_component_id: int):
    with database.get_session_ctx() as session:
        instance_component = session.get(M.InstanceComponent, instance_component_id)
        session.delete(instance_component)
        session.commit()
