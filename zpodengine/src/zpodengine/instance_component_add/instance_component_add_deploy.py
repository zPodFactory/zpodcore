from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.ovfdeployer import ovf_deployer
from zpodcommon.lib.vcsadeployer import vcsa_deployer
from zpodcommon.lib.vmware import vCenter
from zpodengine.instance_component_add.instance_component_add_utils import (
    handle_instance_component_add_failure,
)
from zpodengine.lib import database


@task
@handle_instance_component_add_failure
def instance_component_add_deploy(*, instance_component_id: int):
    print("Deploy OVA")
    with database.get_session_ctx() as session:
        instance_component = session.get(M.InstanceComponent, instance_component_id)

        c = instance_component.component
        print(c)

        match c.component_name:
            case "zbox":
                print("--- zbox ---")

                ovf_deployer(instance_component)

                vm_name = f"{c.component_name}.{instance_component.instance.domain}"
                print(vm_name)

                with vCenter.auth_by_instance(
                    instance=instance_component.instance
                ) as vc:
                    # Add second disk for NFS filer to VM
                    # 100GB = 104,857,600 KB
                    # 1TB = 1,073,741,824 KB
                    print("Add Second Disk")
                    vc.add_disk_to_vm(vm_name=vm_name, disk_size_in_kb=1073741824)
                    # Power On VM
                    print("PowerOn VM")
                    vc.poweron_vm(vm_name=vm_name)

            case "vyos":
                print("--- vyos ---")
                # Add static routes on NSX T1

            case "vcsa":
                print("--- vcsa ---")
                # Prep component ISO to folder
                # Prep deploy template from component json
                vcsa_deployer(instance_component)

            case "esxi":
                print("--- esxi ---")
                # post configuration (sizing / disks, etc)

                ovf_deployer(instance_component)

                vcpu = instance_component.data["vcpu"]
                vmem = instance_component.data["vmem"]

                print(f"VM resizing to {vcpu} CPUs, and {vmem}GB Memory")

                if "hostname" in instance_component.data:
                    zpod_hostname = instance_component.data["hostname"]
                elif "last_octet" in instance_component.data:
                    zpod_hostname = (
                        f"{c.component_name}{instance_component.data['last_octet']}"
                    )
                else:
                    zpod_hostname = c.component_name

                vm_name = f"{zpod_hostname}.{instance_component.instance.domain}"
                print(vm_name)

                with vCenter.auth_by_instance(
                    instance=instance_component.instance
                ) as vc:
                    print("Set CPU")
                    vc.set_vm_vcpu(vm_name=vm_name, vcpu_num=vcpu)
                    print("Set Memory")
                    vc.set_vm_vmem(vm_name=vm_name, vmem_gb=vmem)
                    print("Start VM")
                    vc.poweron_vm(vm_name=vm_name)

            case _:
                print("--- Normal Component ---")
                ovf_deployer(instance_component)

                instance_vc = vCenter(
                    host=f"vcsa.{instance_component.instance.domain}",
                    user=f"administrator@{instance_component.instance.domain}",
                    pwd=instance_component.instance.password,
                )

                print("Start VM")
                instance_vc.poweron_vm(
                    vm_name=instance_component.component.component_name
                )
