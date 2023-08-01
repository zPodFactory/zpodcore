from prefect import task
from sqlmodel import select

from zpodcommon import models as M
from zpodcommon.lib.commands import cmd_execute
from zpodcommon.lib.dbutils import DBUtils
from zpodcommon.lib.network import MgmtIp
from zpodcommon.lib.vmware import vCenter
from zpodengine.instance_component_add.instance_component_add_utils import (
    handle_instance_component_add_failure,
)
from zpodengine.lib import database


@task
@handle_instance_component_add_failure
def instance_component_add_post_scripts(*, instance_component_id: int):
    with database.get_session_ctx() as session:
        instance_component = session.get(M.InstanceComponent, instance_component_id)
        custom_postscripts = instance_component.data.get("postscripts", [])
        print(f"Run Postscripts: {custom_postscripts}")

        zpodfactory_host = DBUtils.get_setting_value("zpodfactory_host")

        c = instance_component.component
        i = instance_component.instance

        if _ := instance_component.data.get("hostname"):
            zpod_hostname = _
        elif _ := instance_component.data.get("last_octet"):
            zpod_hostname = f"{c.component_name}{_}"
        else:
            zpod_hostname = c.component_name

        # Specific behavior for critical instance components
        match c.component_name:
            case "zbox":
                print("--- zbox ---")

                # Add static routes on NSX T1 unless using vyos below

            case "vyos":
                print("--- vyos ---")
                # Add static routes on NSX T1
                # Potentially move DNS and other facilities to this later on

            case "vcsa":
                print("--- vcsa ---")

                # Fetch list of esxi components attached to this instance
                zpod_esxi_list = [
                    f"esxi{cur_component.data.get('last_octet')}.{i.domain}"
                    for cur_component in i.components
                    if cur_component.component.component_name == "esxi"
                ]

                # Configure vcsa component
                cmd = (
                    f"/zpodengine/scripts/powershell/post-scripts/vcsa_configure.ps1"
                    f" -zPodHostname {zpod_hostname}.{i.domain}"
                    f" -zPodUsername administrator@{i.domain}"
                    f" -zPodPassword {i.password}"
                    f" -zPodESXiList {','.join(zpod_esxi_list)}"
                )
                cmd_execute(f'pwsh -c "& {cmd}"', debug=True)

            case "esxi":
                print("--- esxi ---")

                with vCenter.auth_by_instance(
                    instance=instance_component.instance
                ) as vc:
                    component_ipaddress = MgmtIp.instance_component(
                        instance_component
                    ).ip

                    print(f"Waiting for VMware Tools IP {component_ipaddress}...")
                    vc.wait_for_tools_ip(
                        f"{zpod_hostname}.{i.domain}", component_ipaddress
                    )

                # Check esxi host ssl certificate regeneration has been done before continuing
                cmd = (
                    f"/zpodengine/scripts/python/post-scripts/esxi_check_certificate.py"
                    f" {zpod_hostname}.{i.domain} {zpod_hostname}"
                )

                cmd_execute(f"python {cmd}", debug=True)

                # Configure esxi
                cmd = (
                    f"/zpodengine/scripts/powershell/post-scripts/esxi_configure.ps1"
                    f" -zPodHostname {zpod_hostname}.{i.domain}"
                    f" -zBoxHostname zbox.{i.domain}"
                    f" -zPodFactory {zpodfactory_host}.{i.domain}"
                    f" -zPodPassword {i.password}"
                )
                cmd_execute(f'pwsh -c "& {cmd}"', debug=True)

            case _:
                print("Normal component, nothing to do here yet...")
