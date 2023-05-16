from prefect import task

from zpodcommon import models as M
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

        c = instance_component.component
        print(c)

        # Specific behavior for critical instance components

        match c.component_name:
            case "zbox":
                print("--- zbox ---")

                vm_name = f"{c.component_name}.{instance_component.instance.domain}"
                print(vm_name)

                with vCenter.auth_by_instance(
                    instance=instance_component.instance
                ) as vc:
                    # Add second disk for NFS filer to VM
                    # 1TB = 104,857,600 KB
                    print("Add Second Disk")
                    vc.add_disk_to_vm(vm_name=vm_name, disk_size_in_kb=104857600)
                    # Power On VM
                    print("PowerOn VM")
                    vc.poweron_vm(vm_name=vm_name)

            case "vyos":
                print("vyos")
                # Add static routes on NSX T1

            case "vcsa":
                print("vcsa")
                # Wait for vcsa to be deployed if not using vcsa-cli-installer (ova only)

            case "esxi":
                print("esxi")
                # post configuration (sizing / disks, etc)

            case _:
                print("Normal component, nothing to do here yet...")
