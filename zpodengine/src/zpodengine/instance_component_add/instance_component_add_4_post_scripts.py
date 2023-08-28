from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.commands import cmd_execute
from zpodcommon.lib.dbutils import DBUtils
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

        zpodfactory_host = DBUtils.get_setting_value("zpodfactory_host")

        component = instance_component.component
        instance = instance_component.instance

        # Specific behavior for critical instance components
        match component.component_name:
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
                    cur_component.fqdn
                    for cur_component in instance.components
                    if cur_component.component.component_name == "esxi"
                ]

                # Fetch vCenter Server Licenses from Settings
                license_parts = []
                license_vcenter = DBUtils.get_component_license(component, "vcenter")
                if license_vcenter is not None:
                    license_parts.append(f"-license_vcenter {license_vcenter}")

                license_esxi = DBUtils.get_component_license(component, "esxi")
                if license_esxi is not None:
                    license_parts.append(f"-license_esxi {license_esxi}")

                license_vsan = DBUtils.get_component_license(component, "vsan")
                if license_vsan is not None:
                    license_parts.append(f"-license_vsan {license_vsan}")

                license_tanzu = DBUtils.get_component_license(component, "tanzu")

                if license_tanzu is not None:
                    license_parts.append(f"-license_tanzu {license_tanzu}")

                # Configure vcsa component
                cmd = (
                    f"/zpodengine/scripts/powershell/post-scripts/vcsa_configure.ps1"
                    f" -zPodHostname {instance_component.fqdn}"
                    f" -zPodUsername administrator@{instance.domain}"
                    f" -zPodPassword {instance.password}"
                    f" -zPodESXiList {','.join(zpod_esxi_list)}"
                    " " + " ".join(license_parts)
                )
                cmd_execute(f'pwsh -c "& {cmd}"')

            case "esxi":
                print("--- esxi ---")

                with vCenter.auth_by_instance(
                    instance=instance_component.instance
                ) as vc:
                    print(f"Waiting for VMware Tools IP {instance_component.ip}...")
                    vc.wait_for_tools_ip(
                        f"{instance_component.fqdn}", instance_component.ip
                    )

                # Check esxi host ssl certificate regeneration has been done before
                # continuing
                cmd = (
                    f"/zpodengine/scripts/python/post-scripts/esxi_check_certificate.py"
                    f" {instance_component.fqdn} {instance_component.hostname}"
                )

                cmd_execute(f"python {cmd}")

                # Configure esxi
                cmd = (
                    f"/zpodengine/scripts/powershell/post-scripts/esxi_configure.ps1"
                    f" -zPodHostname {instance_component.fqdn}"
                    f" -zBoxHostname zbox.{instance.domain}"
                    f" -zPodFactory {zpodfactory_host}.{instance.domain}"
                    f" -zPodPassword {instance.password}"
                )
                cmd_execute(f'pwsh -c "& {cmd}"')

            case _:
                print("Normal component, nothing to do here yet...")
