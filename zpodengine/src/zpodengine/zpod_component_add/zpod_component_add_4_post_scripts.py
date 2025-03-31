import datetime
import time

from prefect import task

from zpodcommon import models as M
from zpodcommon.enums import ZpodComponentStatus
from zpodcommon.lib.dbutils import DBUtils
from zpodcommon.lib.nsx import NsxClient
from zpodcommon.lib.vmware import vCenter
from zpodcommon.lib.zboxapi import HTTPStatusError, RequestError, ZboxApiClient
from zpodengine.lib import database
from zpodengine.lib.commands import cmd_execute
from zpodengine.zpod_component_add.zpod_component_add_utils import (
    handle_zpod_component_add_failure,
    set_zpod_component_status,
)


@task
@handle_zpod_component_add_failure
def zpod_component_add_post_scripts(*, zpod_component_id: int):
    set_zpod_component_status(zpod_component_id, ZpodComponentStatus.POST_SCRIPTS)
    with database.get_session_ctx() as session:
        zpod_component = session.get(M.ZpodComponent, zpod_component_id)

        zpodfactory_host = DBUtils.get_setting_value("zpodfactory_host")

        component = zpod_component.component
        zpod = zpod_component.zpod

        # Specific behavior for critical zpod components
        match component.component_name:
            case "zbox":
                print("--- zbox ---")
                # Add static routes on NSX T1 unless using vyos below

                # Wait until zboxapi is ready
                zb = ZboxApiClient.by_zpod(zpod)
                timeout = datetime.timedelta(seconds=180)
                finish_time = datetime.datetime.now(datetime.UTC) + timeout
                while finish_time > datetime.datetime.now(datetime.UTC):
                    try:
                        response = zb.get(url="/dns")
                        response.raise_for_status()
                        return
                    except (RequestError, HTTPStatusError) as e:
                        print(f"Waiting for {e.request.url} to start.")
                        time.sleep(15)

                # Would prefer to raise an error here, but we need to support old
                # zbox versions
                print("DNS startup failure.  Skipping...")

            case "vyos":
                print("--- vyos ---")
                # Add static routes on NSX T1
                # Potentially move DNS and other facilities to this later on

            case "vcsa":
                print("--- vcsa ---")

                # Fetch list of esxi components attached to this zpod
                zpod_esxi_list = [
                    cur_component.fqdn
                    for cur_component in zpod.components
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
                    f" -zPodHostname {zpod_component.fqdn}"
                    f" -zPodUsername administrator@{zpod.domain}"
                    f" -zPodPassword {zpod.password}"
                    f" -zPodESXiList {','.join(zpod_esxi_list)}"
                    " " + " ".join(license_parts)
                )
                cmd_execute(f'pwsh -c "& {cmd}"').check_returncode()

            case "esxi":
                print("--- esxi ---")

                with vCenter.auth_by_zpod_endpoint(zpod=zpod_component.zpod) as vc:
                    vc.wait_for_tools_ip(f"{zpod_component.fqdn}", zpod_component.ip)

                # Check esxi host ssl certificate regeneration has been done before
                # continuing
                cmd = (
                    f"/zpodengine/scripts/python/post-scripts/esxi_check_certificate.py"
                    f" {zpod_component.fqdn} {zpod_component.hostname}"
                )

                cmd_execute(f"python {cmd}").check_returncode()

                # Configure esxi
                cmd = (
                    f"/zpodengine/scripts/powershell/post-scripts/esxi_configure.ps1"
                    f" -zPodHostname {zpod_component.fqdn}"
                    f" -zBoxHostname zbox.{zpod.domain}"
                    f" -zPodFactory {zpodfactory_host}.{zpod.domain}"
                    f" -zPodPassword {zpod.password}"
                )
                cmd_execute(f'pwsh -c "& {cmd}"').check_returncode()

            case "nsx":
                print("--- nsx ---")

                with vCenter.auth_by_zpod(zpod=zpod) as vc:
                    vc.wait_for_tools_ip(
                        vm_name=zpod_component.hostname, ipaddress=zpod_component.ip
                    )

                license_nsx = DBUtils.get_component_license(component, "enterprise")
                if license_nsx is not None:
                    retries = 60
                    wait_time = 60
                    nsx_is_ready = False
                    for retry in range(retries):
                        try:
                            nsx = NsxClient.auth_by_zpod(zpod=zpod_component.zpod)
                            response = nsx.get(url="/api/v1/cluster/status")
                            nsx_status = (
                                response.safejson()
                                .get("mgmt_cluster_status")
                                .get("status")
                            )
                            print(f"NSX management cluster status is {nsx_status}")
                            if nsx_status != "STABLE":
                                raise ValueError(
                                    f"NSX management cluster status is {nsx_status}"
                                )
                            if (
                                DBUtils.get_setting_value(
                                    "ff_component_wait_for_status"
                                )
                                == "true"
                            ):
                                nsx_overall_status = (
                                    response.safejson()
                                    .get("detailed_cluster_status")
                                    .get("overall_status")
                                )
                                print(f"NSX overall cluster status is {nsx_status}")
                                if nsx_overall_status != "STABLE":
                                    raise ValueError(
                                        f"NSX overall cluster status is {nsx_status}"
                                    )
                            nsx_is_ready = True
                            break
                        except (RequestError, HTTPStatusError) as e:
                            print(
                                f"Waiting for {e.request.url} {e} - Retry {retry}/{retries}"
                            )
                            print("Sleeping...")
                            time.sleep(wait_time)
                        except ValueError as e:
                            print(f"{e} - Retry {retry}/{retries}")
                            print("Sleeping...")
                            time.sleep(wait_time)
                    if not nsx_is_ready:
                        raise ValueError(
                            f"NSX management cluster not ready after {retries} retries"
                        )

                    print(f"Setting license key {license_nsx} on NSX")
                    response = nsx.post(
                        url="/api/v1/licenses",
                        json={
                            "license_key": license_nsx,
                        },
                    )
                    response.safejson()
                    print("License key set successfully on NSX")
            case _:
                print("Normal component, nothing to do here yet...")
