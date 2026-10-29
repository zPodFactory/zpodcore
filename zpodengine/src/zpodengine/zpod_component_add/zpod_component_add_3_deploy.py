from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.component_placement import component_isnested
from zpodcommon.lib.vmware import vCenter
from zpodengine.lib import database
from zpodengine.lib.datastore_floor import check_endpoint_datastore_floor
from zpodengine.lib.ovfdeployer import ovf_deployer
from zpodengine.lib.vcsadeployer import vcsa_deployer
from zpodengine.zpod_component_add.zpod_component_add_utils import (
    handle_zpod_component_add_failure,
)
from zpodengine.zpod_disk.common import ensure_deploy_rows

ZCORE_FILER_DISK_GB = 1024


@task
@handle_zpod_component_add_failure
def zpod_component_add_deploy(
    *,
    zpod_component_id: int,
    vcpu: int | None = None,
    vmem: int | None = None,
    vnics: int | None = None,
    vdisks: list[int] | None = None,
    nested: bool | None = None,
    network: dict | None = None,
    vlan_id: int | None = None,
):
    print("Deploy OVA")
    with database.get_session_ctx() as session:
        zpod_component = session.get(M.ZpodComponent, zpod_component_id)

        component = zpod_component.component
        print(component)

        # L1 components land on the endpoint's datastore: its floor first (D11).
        if not component_isnested(component.component_json, nested):
            check_endpoint_datastore_floor(
                zpod_component.zpod,
                f"component add {zpod_component.zpod.name}/{zpod_component.hostname}",
            )

        match component.component_name:
            case "zcore":
                print("--- zcore ---")

                ovf_deployer(zpod_component, vlan_id=vlan_id)

                with vCenter.auth_by_zpod_endpoint(zpod=zpod_component.zpod) as vc:
                    vm = vc.get_vm(name=zpod_component.fqdn)
                    # Each disk's UUID becomes its serial in zcore, which is how the
                    # disk flows find a disk there; read at the first power-on.
                    if vc.set_disk_enable_uuid(vm):
                        print("Set disk.EnableUUID (not in the OVA)")
                    # The filer disk, formatted by zcore-init as STORAGE01.
                    print("Add Second Disk (1024 GiB, SCSI 0:1)")
                    vc.add_vdisk(vm, ZCORE_FILER_DISK_GB, unit=1)
                    ensure_deploy_rows(session, zpod_component.zpod, vc, vm)
                    # Power On VM
                    print("PowerOn VM")
                    vc.poweron_vm(vm)

            case "vyos":
                print("--- vyos ---")
                # Add static routes on NSX T1

            case "cloudbuilder" | "vcfinstaller":
                print(f"--- {component.component_name} ---")

                ovf_deployer(zpod_component, vlan_id=vlan_id)

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

            case "esxi" | "proxmox":
                print("--- hypervisor ---")
                # post configuration (sizing / disks, etc)

                ovf_deployer(zpod_component, vlan_id=vlan_id)

                with vCenter.auth_by_zpod_endpoint(zpod=zpod_component.zpod) as vc:
                    vm = vc.get_vm(name=zpod_component.fqdn)
                    vc.set_vm_configuration(
                        vm=vm,
                        vcpu=vcpu,
                        vmem_gb=vmem,
                        vnic_num=vnics,
                        vdisks_gb=vdisks,
                    )
                    print("Start VM")
                    vc.poweron_vm(vm)

            # Proxmox Datacenter Manager and Proxmox Backup Server are deployed non nested
            case "proxmox-dm" | "proxmox-bs":
                print("--- proxmox components ---")

                ovf_deployer(zpod_component, vlan_id=vlan_id)

                with vCenter.auth_by_zpod_endpoint(zpod=zpod_component.zpod) as vc:
                    vm = vc.get_vm(name=zpod_component.fqdn)

                    # Set VM configuration
                    vc.set_vm_configuration(
                        vm=vm,
                        vcpu=vcpu,
                        vmem_gb=vmem,
                        vnic_num=vnics,
                        vdisks_gb=vdisks,
                    )

                    print("Start VM")
                    vc.poweron_vm(vm)

            case _:
                print("--- Normal Component ---")
                ovf_deployer(
                    zpod_component, nested=nested, network=network, vlan_id=vlan_id
                )

                isnested = component_isnested(component.component_json, nested)
                print(f"Component Nested: {isnested}")

                auth = (
                    vCenter.auth_by_zpod if isnested else vCenter.auth_by_zpod_endpoint
                )
                vm_name = zpod_component.hostname if isnested else zpod_component.fqdn

                with auth(zpod=zpod_component.zpod) as vc:
                    vm = vc.get_vm(name=vm_name)

                    print("Set VM Configuration")
                    vc.set_vm_configuration(
                        vm=vm,
                        vcpu=vcpu,
                        vmem_gb=vmem,
                        vnic_num=vnics,
                        vdisks_gb=vdisks,
                    )

                    print("Start VM")
                    vc.poweron_vm(vm)
