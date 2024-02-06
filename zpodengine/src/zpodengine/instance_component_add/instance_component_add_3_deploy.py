from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.vmware import vCenter
from zpodengine.instance_component_add.instance_component_add_utils import (
    handle_instance_component_add_failure,
)
from zpodengine.lib import database
from zpodengine.lib.ovfdeployer import ovf_deployer
from zpodengine.lib.vcsadeployer import vcsa_deployer


@task
@handle_instance_component_add_failure
def instance_component_add_deploy(
    *,
    instance_component_id: int,
    vcpu: int | None = None,
    vmem: int | None = None,
    vdisks: list[int] | None = None,
):
    print("Deploy OVA")
    with database.get_session_ctx() as session:
        instance_component = session.get(M.InstanceComponent, instance_component_id)

        component = instance_component.component
        print(component)

        match component.component_name:
            case "zbox":
                print("--- zbox ---")

                ovf_deployer(instance_component)

                with vCenter.auth_by_instance_endpoint(
                    instance=instance_component.instance
                ) as vc:
                    vm = vc.get_vm(name=instance_component.fqdn)
                    # Add second disk for NFS filer to VM
                    # 100GB = 104,857,600 KB
                    # 1TB = 1,073,741,824 KB
                    print("Add Second Disk")
                    vc.add_disk_to_vm(vm=vm, disk_size_in_kb=1073741824)
                    # Power On VM
                    print("PowerOn VM")
                    vc.poweron_vm(vm)

            case "vyos":
                print("--- vyos ---")
                # Add static routes on NSX T1

            case "vcf":
                print("--- vcf ---")

                ovf_deployer(instance_component)

                with vCenter.auth_by_instance_endpoint(
                    instance=instance_component.instance
                ) as vc:
                    vm = vc.get_vm(name=instance_component.fqdn)
                    # Power On VM
                    print("PowerOn VM")
                    vc.poweron_vm(vm)

            case "vcsa":
                print("--- vcsa ---")
                # Prep component ISO to folder
                # Prep deploy template from component json
                vcsa_deployer(instance_component)

            case "esxi":
                print("--- esxi ---")
                # post configuration (sizing / disks, etc)

                ovf_deployer(instance_component)

                print(f"VM resizing to {vcpu} CPUs, and {vmem}GB Memory")

                with vCenter.auth_by_instance_endpoint(
                    instance=instance_component.instance
                ) as vc:
                    vm = vc.get_vm(name=instance_component.fqdn)
                    if vcpu:
                        print("Set CPU")
                        vc.set_vm_vcpu(vm=vm, vcpu_num=vcpu)
                    if vmem:
                        print("Set Memory")
                        vc.set_vm_vmem(vm=vm, vmem_gb=vmem)
                    if vdisks:
                        for disk_number, vdisk_gb in enumerate(vdisks, 2):
                            print(f"Resize Hard disk {disk_number}")
                            vc.set_vm_vdisk(
                                vm=vm,
                                vdisk_gb=vdisk_gb,
                                disk_number=disk_number,
                            )
                    print("Start VM")
                    vc.poweron_vm(vm)

            case _:
                with vCenter(
                    host=f"vcsa.{instance_component.instance.domain}",
                    user=f"administrator@{instance_component.instance.domain}",
                    pwd=instance_component.instance.password,
                ) as vc:
                    print("--- Normal Component ---")
                    ovf_deployer(instance_component)

                    vm = vc.get_vm(name=instance_component.hostname)
                    print("Start VM")
                    vc.poweron_vm(vm)
