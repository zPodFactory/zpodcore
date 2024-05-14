import json

from prefect import flow, task

from zpodcommon import models as M
from zpodcommon.lib.vmware import vCenter
from zpodcommon.lib.zboxapi import HTTPStatusError, RequestError, ZboxApiClient
from zpodengine import settings
from zpodengine.lib import database
from zpodengine.lib.utils import ctx_param


def set_flow_name():
    with database.get_session_ctx() as session:
        zpod_component = session.get(
            M.ZpodComponent,
            ctx_param("zpod_component_id"),
        )
        return (
            f"Remove zPod Component {zpod_component.zpod.name} "
            f"{zpod_component.hostname}"
        )


@flow(
    name="zpod_component_remove",
    flow_run_name=set_flow_name,
    log_prints=True,
)
def flow_zpod_component_remove(
    zpod_component_id: int,
):
    dns = remove_from_dns.submit(zpod_component_id)
    vc = remove_from_vcenter.submit(zpod_component_id)
    remove_from_db.submit(zpod_component_id, wait_for=[dns, vc])


@task()
def remove_from_dns(zpod_component_id: int):
    with database.get_session_ctx() as session:
        zpod_component = session.get(M.ZpodComponent, zpod_component_id)

        zb = ZboxApiClient.by_zpod(zpod_component.zpod)
        try:
            # Used .request(method=DELETE), because
            # .delete() doesn't allow passing json
            response = zb.request(
                method="DELETE",
                url="/hosts",
                json={
                    "ip": zpod_component.ip,
                    "fqdn": zpod_component.hostname,
                },
            )
            response.raise_for_status()
        except (RequestError, HTTPStatusError):
            print(f"{zb.base_url} failure.  Skipping...")


@task()
def remove_from_vcenter(zpod_component_id: int):
    with database.get_session_ctx() as session:
        zpod_component = session.get(M.ZpodComponent, zpod_component_id)

        # Open Component JSON file
        f = open(zpod_component.component.jsonfile)

        # Load component JSON
        cjson = json.load(f)

        zpod = zpod_component.zpod
        if cjson["component_isnested"]:
            with vCenter.auth_by_zpod(zpod=zpod) as vc:
                vc.delete_vm_nested(
                    domain_name=zpod.domain,
                    vm_name=zpod_component.hostname,
                )
        else:
            with vCenter.auth_by_zpod_endpoint(zpod=zpod) as vc:
                vc.delete_vm_from_vapp(
                    vapp_name=f"{settings.SITE_ID}-{zpod.name}",
                    vm_name=zpod_component.fqdn,
                )


@task()
def remove_from_db(zpod_component_id: int):
    with database.get_session_ctx() as session:
        zpod_component = session.get(M.ZpodComponent, zpod_component_id)
        session.delete(zpod_component)
        session.commit()
