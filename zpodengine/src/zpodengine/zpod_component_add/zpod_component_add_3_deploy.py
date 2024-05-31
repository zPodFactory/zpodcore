from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.vmware import vCenter
from zpodengine.lib import database
from zpodengine.lib.ovfdeployer import ovf_deployer
from zpodengine.lib.vcsadeployer import vcsa_deployer
from zpodengine.zpod_component_add.zpod_component_add_utils import (
    handle_zpod_component_add_failure,
)


@task
@handle_zpod_component_add_failure
def zpod_component_add_deploy(
    *,
    zpod_component_id: int,
    vcpu: int | None = None,
    vmem: int | None = None,
    vdisks: list[int] | None = None,
):
    print("Deploy OVA")
    with database.get_session_ctx() as session:
        zpod_component = session.get(M.ZpodComponent, zpod_component_id)

        component = zpod_component.component
        print(component)

        match component.component_name:
            case "zbox":
                print("--- zbox ---")

                ovf_deployer(zpod_component)

                with vCenter.auth_by_zpod_endpoint(zpod=zpod_component.zpod) as vc:
                    vm = vc.get_vm(name=zpod_component.fqdn)
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

            case "cloudbuilder":
                print("--- cloudbuilder ---")

                ovf_deployer(zpod_component)

                with vCenter.auth_by_zpod_endpoint(zpod=zpod_component.zpod) as vc:
                    vm = vc.get_vm(name=zpod_component.fqdn)
                    # Power On VM
                    print("PowerOn VM")
                    vc.poweron_vm(vm)

            case "vcsa":
                print("--- vcsa ---")
                # Prep component ISO to folder
                # Prep deploy template from component json
                vcsa_deployer(zpod_component)

            case "esxi":
                print("--- esxi ---")
                # post configuration (sizing / disks, etc)

                ovf_deployer(zpod_component)

                print(f"VM resizing to {vcpu} CPUs, and {vmem}GB Memory")

                with vCenter.auth_by_zpod_endpoint(zpod=zpod_component.zpod) as vc:
                    vm = vc.get_vm(name=zpod_component.fqdn)
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
                print("--- Normal Component ---")
                ovf_deployer(zpod_component)

                with vCenter.auth_by_zpod(zpod=zpod_component.zpod) as vc:
                    vm = vc.get_vm(name=zpod_component.hostname)
                    print("Start VM")
                    vc.poweron_vm(vm)
