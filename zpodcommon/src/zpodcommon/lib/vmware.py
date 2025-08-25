import atexit
import datetime
import logging
import ssl
import time
from contextlib import nullcontext

from pyVim import connect, task
from pyVmomi import vim, vmodl

from zpodcommon import models as M
from zpodcommon.lib import database

logger = logging.getLogger(__name__)


class vCenter:
    def __init__(self, host=None, user=None, pwd=None):
        self.host = host
        self.user = user
        self.pwd = pwd
        self.si = None
        self.connect()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.disconnect()

    def connect(self):
        self.si = None
        try:
            print(f"Initializing vCenter connection {self.host} with user {self.user}")
            self.si = connect.SmartConnect(
                host=self.host,
                user=self.user,
                pwd=self.pwd,
                sslContext=ssl._create_unverified_context(),
            )
            atexit.register(connect.Disconnect, self.si)
        except vim.fault.InvalidLogin as e:
            raise ConnectionError("Invalid username or password.") from e
        except IOError as e:
            raise ConnectionError(f"Unable to connect to host: {self.host}.") from e

    def create_filter_spec(self, pc, data, props, vimtype):
        filterSpec = vmodl.query.PropertyCollector.FilterSpec()
        filterSpec.objectSet = [
            vmodl.query.PropertyCollector.ObjectSpec(obj=d) for d in data
        ]
        propSet = vmodl.query.PropertyCollector.PropertySpec(all=False)
        propSet.type = vimtype
        propSet.pathSet = props
        filterSpec.propSet = [propSet]
        return filterSpec

    def disconnect(self):
        connect.Disconnect(self.si)

    def joinitems(self, *args):
        ret = []
        for arg in args:
            if isinstance(arg, str):
                ret.append(arg)
            elif isinstance(arg, list):
                ret.extend(arg)
        return ret

    def get_obj(self, vimtype, attr, value, root=None, props=None):
        objs = self.get_obj_list(vimtype, root=root)
        info = [
            oprops if props else oprops["obj"]
            for oprops in self.get_props(data=objs, props=self.joinitems(attr, props))
            if oprops[attr] == value
        ]
        li = len(info)
        if li == 1:
            return info[0]
        elif li == 0:
            return None
        raise Exception("Multiple results found when there should only be one")

    def get_obj_list(self, vimtype, root=None, props=None):
        if root is None:
            root = self.si.content.rootFolder

        container = self.si.content.viewManager.CreateContainerView(
            root, [vimtype], True
        )
        view = container.view
        container.Destroy()
        return self.get_props(data=view, props=props) if props else view

    def get_portgroups(self, props=None):
        return self.get_obj_list([vim.Network], props=props)

    def get_portgroup(self, name, props=None):
        return self.get_obj(vim.Network, "name", name, props=props)

    def get_props(self, data, props):
        if not data:
            return []
        if not isinstance(props, list):
            props = [props]

        pc = self.si.content.propertyCollector
        filter_spec = self.create_filter_spec(pc, data, props, type(data[0]))
        options = vmodl.query.PropertyCollector.RetrieveOptions()
        result = pc.RetrievePropertiesEx([filter_spec], options)
        ret = self.gather_prop_results(result)
        while result.token:
            result = pc.ContinueRetrievePropertiesEx(token=result.token)
            ret.extend(self.gather_prop_results(result))
        return ret

    def gather_prop_results(self, result):
        ret = []
        for o in result.objects:
            item = {"obj": o.obj}
            for p in o.propSet:
                item[p.name] = p.val
            ret.append(item)
        return ret

    def find_folder(self, name, folder):
        if folder.name == name:
            return folder
        for child in folder.childEntity:
            if isinstance(child, vim.Folder):
                if result := self.find_folder(name, child):
                    return result

    def get_vapps(self, root=None, props=None):
        return self.get_obj_list(vim.VirtualApp, root=root, props=props)

    def get_vapp(self, name, root=None, props=None):
        return self.get_obj(vim.VirtualApp, "name", name, root=root, props=props)

    def get_vms(self, root=None, props=None):
        return self.get_obj_list(vim.VirtualMachine, root=root, props=props)

    def get_vm(self, name, root=None, props=None):
        return self.get_obj(vim.VirtualMachine, "name", name, root=root, props=props)

    def create_allocation_object(self, resSpec, value):
        result = vim.ResourceAllocationInfo()
        result.shares = vim.SharesInfo()
        result.shares.shares = value
        result.shares.level = vim.SharesInfo.Level.normal
        result.limit = -1
        result.reservation = 0
        result.expandableReservation = True
        return result

    def create_vapp(self, vapp_name, resource_pool_name, folder_name):
        content = self.si.content

        resource_pool = None

        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.ClusterComputeResource, vim.ResourcePool], True
        )

        for _resource_pool in container.view:
            if _resource_pool.name == resource_pool_name:
                if isinstance(_resource_pool, vim.ClusterComputeResource):
                    resource_pool = _resource_pool.resourcePool
                else:
                    resource_pool = _resource_pool

        folders = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.Folder], True
        ).view
        vmFolderMO = None

        for folder in folders:
            if isinstance(folder, vim.Folder):
                if result := self.find_folder(folder_name, folder):
                    vmFolderMO = result
                    break

        resSpec = vim.ResourceConfigSpec()
        resSpec.memoryAllocation = self.create_allocation_object(resSpec, 163840)
        resSpec.cpuAllocation = self.create_allocation_object(resSpec, 4000)
        configSpec = vim.vApp.VAppConfigSpec()
        configSpec.entityConfig = []
        configSpec.property = []

        resource_pool.CreateVApp(vapp_name, resSpec, configSpec, vmFolderMO)

    def delete_vapp(self, vapp_name):
        if vapp := self.get_vapp(vapp_name):
            if vapp.summary.vAppState != "stopped":
                # Wait for vApp PowerOff operation to complete
                task_id = vapp.PowerOffVApp_Task(True)
                task.WaitForTask(task_id)

            # Wait for vApp Destroy operation to complete
            task_id = vapp.Destroy_Task()
            task.WaitForTask(task_id)

    def delete_vm_from_vapp(self, vapp_name: str, vm_name: str):
        print("Delete VM from vApp")
        if vapp := self.get_vapp(name=vapp_name):
            # Verify vm is in vapp
            if vm := self.get_vm(name=vm_name, root=vapp):
                self.delete_vm(vm)
            else:
                print(
                    f"VM: {vm_name} not found in "
                    f"vApp: {vapp_name} on vCenter: ({self.host})"
                )
        else:
            print(f"vApp: {vapp_name} not found in vCenter ({self.host}): {vapp_name}")

    def delete_vm_nested(self, domain_name: str, vm_name: str):
        print("Delete NESTED VM")
        if vm := self.get_vm(name=vm_name):
            esxi_hostname = vm.runtime.host.name
            # Validate that the host name running the vm
            # contains the specified domain name (Verify
            # that we are on the correct vCenter)
            if esxi_hostname.endswith(f".{domain_name}"):
                self.delete_vm(vm)
            else:
                print(
                    f"Domain Name: {domain_name} not found "
                    f"in esxi hostname {esxi_hostname}"
                )
        else:
            print(f"VM not found in vCenter ({self.host}): {vm_name}")

    def delete_vm(self, vm: vim.VirtualMachine):
        # Make sure vm is powered off
        self.poweroff_vm(vm=vm)

        print(f"Deleting vm: {vm.name}")

        # Delete the VM
        task_id = vm.Destroy_Task()

        # Wait for vm Destroy operation to complete
        task.WaitForTask(task_id)

    def poweroff_vm(self, vm: vim.VirtualMachine):
        if vm.runtime.powerState != "poweredOff":
            print(f"Powering off vm: {vm.name}")
            task_id = vm.PowerOffVM_Task()
            task.WaitForTask(task_id)

    def poweron_vm(self, vm: vim.VirtualMachine):
        task_id = vm.PowerOnVM_Task()
        task.WaitForTask(task_id)

    def poweroff_vapp(self, vapp: vim.VirtualApp):
        if vapp and vapp.summary.vAppState != "stopped":
            # Wait for vApp PowerOff operation to complete
            task_id = vapp.PowerOffVApp_Task(True)
            task.WaitForTask(task_id)

    def poweron_vapp(self, vapp: vim.VirtualApp):
        if vapp and vapp.summary.vAppState != "started":
            # We don't need to wait here
            # That means zpod was explictly powered off by a user
            # restart will go through all vms in that vApp anyway.
            vapp.PowerOnVApp_Task(True)

    def set_vm_vcpu(self, vm: vim.VirtualMachine, vcpu_num: int):
        # sourcery skip: class-extract-method
        # Fetch VM
        # For this example:
        # zbox.{instance_name}.{domain}
        spec = vim.vm.ConfigSpec()
        spec.cpuAllocation = vim.ResourceAllocationInfo()
        spec.cpuAllocation.shares = vim.SharesInfo()
        spec.cpuAllocation.shares.shares = 4000
        spec.cpuAllocation.shares.level = "normal"
        spec.numCPUs = vcpu_num
        spec.deviceChange = []
        spec.virtualNuma = vim.vm.VirtualNuma()
        task_id = vm.ReconfigVM_Task(spec)
        task.WaitForTask(task_id)

    def set_vm_vmem(self, vm: vim.VirtualMachine, vmem_gb: int):
        spec = vim.vm.ConfigSpec()
        spec.memoryMB = vmem_gb * 1024
        spec.memoryAllocation = vim.ResourceAllocationInfo()
        spec.memoryAllocation.shares = vim.SharesInfo()
        spec.memoryAllocation.shares.shares = vmem_gb * 1024 * 10
        spec.memoryAllocation.shares.level = "normal"
        spec.deviceChange = []
        spec.virtualNuma = vim.vm.VirtualNuma()
        task_id = vm.ReconfigVM_Task(spec)
        task.WaitForTask(task_id)

    def _clone_dvpg_backing_from(self, nic: vim.vm.device.VirtualEthernetCard):
        """
        Build a new DVPortgroup backing that matches the given NIC's DVPG.
        Raises if the NIC is not DVPG-backed.
        """
        b = nic.backing
        if not isinstance(
            b, vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo
        ):
            raise ValueError(
                f"Unsupported NIC backing type: expected DistributedVirtualPortBackingInfo, got {type(b).__name__}"
            )
        new_backing = (
            vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
        )
        new_backing.port = vim.dvs.PortConnection()
        new_backing.port.portgroupKey = b.port.portgroupKey
        new_backing.port.switchUuid = b.port.switchUuid
        return new_backing

    def set_vm_vnic(self, vm: vim.VirtualMachine, vnic_num: int) -> None:
        """
        Ensure the VM has at least `vnic_num` vNICs.
        - Never removes NICs.
        - If the VM already has >= vnic_num, do nothing.
        - If fewer, add vmxnet3 NICs on the same DVPortgroup as the first NIC.
        - Blocks until the reconfig task completes.
        - Returns nothing.
        """

        print(f"set_vm_vnic:Setting VM {vm.name} to {vnic_num} NIC(s)...")

        devices = vm.config.hardware.device
        current_nics = [
            d for d in devices if isinstance(d, vim.vm.device.VirtualEthernetCard)
        ]
        current_count = len(current_nics)

        if vnic_num <= current_count:
            print(f"VM already has {current_count} NIC(s); no change needed.")
            return

        if current_count == 0:
            raise ValueError("Cannot infer DVPortgroup: VM has no existing NICs.")

        # Mirror the first NIC's DVPG
        dvpg_backing = self._clone_dvpg_backing_from(current_nics[0])

        to_add = vnic_num - current_count

        # Build a pool of existing keys and choose unique negative keys for new devices
        existing_keys = {d.key for d in devices if hasattr(d, "key")}
        next_key = -100
        while next_key in existing_keys:
            next_key -= 1

        device_changes = []
        for _ in range(to_add):
            dev_spec = vim.vm.device.VirtualDeviceSpec()
            dev_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add

            nic = vim.vm.device.VirtualVmxnet3()
            nic.backing = dvpg_backing

            nic.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
            nic.connectable.connected = True
            nic.connectable.startConnected = True
            nic.connectable.allowGuestControl = True

            # Assign a unique negative key to avoid duplicate-key errors across multiple adds
            nic.key = next_key
            next_key -= 1

            dev_spec.device = nic
            device_changes.append(dev_spec)

        spec = vim.vm.ConfigSpec()
        spec.deviceChange = device_changes

        task_id = vm.ReconfigVM_Task(spec)
        task.WaitForTask(task_id)

    def set_vm_vdisk(self, vm: vim.VirtualMachine, vdisk_gb: int, disk_number: int):
        disk_label = f"Hard disk {disk_number}"
        disk_size = int(vdisk_gb) * 1024 * 1024 * 1024
        disk = None
        for device in vm.config.hardware.device:
            if hasattr(device.backing, "fileName"):
                if device.deviceInfo.label == disk_label:
                    disk = device
                    break
        if disk:
            if disk.capacityInBytes < disk_size:
                disk.capacityInBytes = disk_size
                updated_spec = vim.vm.device.VirtualDeviceSpec(
                    device=disk,
                    operation="edit",
                )
                spec = vim.vm.ConfigSpec()
                spec.deviceChange.append(updated_spec)
                task.WaitForTask(vm.Reconfigure(spec))

    def add_disk_to_vm(self, vm: vim.VirtualMachine, disk_size_in_kb: int):
        #
        # Method to add a disk to a vm with specific disk_size_in_kb
        #

        #
        # Prepare spec for second disk
        #
        spec = vim.vm.ConfigSpec()
        spec_deviceChange = vim.vm.device.VirtualDeviceSpec()
        spec_deviceChange.fileOperation = "create"
        spec_deviceChange.device = vim.vm.device.VirtualDisk()
        spec_deviceChange.device.capacityInBytes = disk_size_in_kb * 1024
        spec_deviceChange.device.storageIOAllocation = (
            vim.StorageResourceManager.IOAllocationInfo()
        )
        spec_deviceChange.device.storageIOAllocation.shares = vim.SharesInfo()
        spec_deviceChange.device.storageIOAllocation.shares.shares = 1000
        spec_deviceChange.device.storageIOAllocation.shares.level = "normal"
        spec_deviceChange.device.storageIOAllocation.limit = -1
        spec_deviceChange.device.backing = (
            vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
        )
        spec_deviceChange.device.backing.fileName = ""
        spec_deviceChange.device.backing.thinProvisioned = True
        spec_deviceChange.device.backing.diskMode = "persistent"
        spec_deviceChange.device.controllerKey = 1000
        spec_deviceChange.device.unitNumber = 1
        spec_deviceChange.device.capacityInKB = disk_size_in_kb
        spec_deviceChange.device.deviceInfo = vim.Description()
        spec_deviceChange.device.deviceInfo.summary = "New Hard disk"
        spec_deviceChange.device.deviceInfo.label = "New Hard disk"
        # Really not sure about this one ... (from code capture)
        spec_deviceChange.device.key = -102

        spec_deviceChange.operation = "add"
        spec.deviceChange = [spec_deviceChange]
        spec.virtualNuma = vim.vm.VirtualNuma()

        # Reconfigure VM with new spec
        task_id = vm.ReconfigVM_Task(spec)
        task.WaitForTask(task_id)

    def wait_for_tools(self, vm_name, timeout=120):
        tools_running = False
        start_at = datetime.datetime.now(datetime.UTC)
        timeout = datetime.timedelta(seconds=timeout)

        print(f"Waiting for VMware Tools for VM {vm_name}...")
        while start_at + timeout > datetime.datetime.now(datetime.UTC):
            vm = self.get_vm(vm_name)

            if vm.guest.toolsRunningStatus == "guestToolsRunning":
                return True
            print("Sleeping ...")
            time.sleep(5)

        if not tools_running:
            print("VMware Tools not running and timeout exceeded !")
            return False

    def wait_for_tools_ip(self, vm_name, ipaddress, timeout=120):
        start_at = datetime.datetime.now(datetime.UTC)
        timeout = datetime.timedelta(seconds=timeout)

        # We first need to wait for vmware tools to be ready
        status = self.wait_for_tools(vm_name)
        if not status:
            return False

        print(f"Waiting for VMware Tools IP {ipaddress} on VM {vm_name}...")
        while start_at + timeout > datetime.datetime.now(datetime.UTC):
            vm = self.get_vm(vm_name)

            if vm.guest.ipAddress == ipaddress:
                print(f"IP {ipaddress} found.")
                return True

            print("Sleeping...")
            time.sleep(5)

        if not ipaddress:
            return False

    @classmethod
    def auth_by_endpoint(
        cls,
        endpoint: M.Endpoint | None = None,
        endpoint_id: int | None = None,
        **kwargs,
    ):
        with database.get_session_ctx() if endpoint_id else nullcontext() as session:
            if endpoint_id:
                endpoint = session.get(M.Endpoint, endpoint_id)

            compute = endpoint.endpoints["compute"]
            return cls(
                host=compute["hostname"],
                user=compute["username"],
                pwd=compute["password"],
                **kwargs,
            )

    @classmethod
    def auth_by_zpod_endpoint(
        cls,
        zpod: M.Zpod | None = None,
        zpod_id: int | None = None,
        **kwargs,
    ):
        with database.get_session_ctx() if zpod_id else nullcontext() as session:
            if zpod_id:
                zpod = session.get(M.Zpod, zpod_id)
            return cls.auth_by_endpoint(endpoint=zpod.endpoint, **kwargs)

    @classmethod
    def auth_by_zpod(
        cls,
        zpod: M.Zpod | None = None,
        zpod_id: int | None = None,
        **kwargs,
    ):
        with database.get_session_ctx() if zpod_id else nullcontext() as session:
            if zpod_id:
                zpod = session.get(M.Zpod, zpod_id)
            return cls(
                host=f"vcsa.{zpod.domain}",
                user=f"administrator@{zpod.domain}",
                pwd=zpod.password,
                **kwargs,
            )
