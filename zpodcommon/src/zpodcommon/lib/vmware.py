import atexit
import datetime
import logging
import ssl
import time

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
        objs = self.get_obj_list([vimtype], root=root)
        return next(
            (
                oprops if props else oprops["obj"]
                for oprops in self.get_props(
                    data=objs, props=self.joinitems(attr, props)
                )
                if oprops[attr] == value
            ),
            None,
        )

    def get_obj_list(self, vimtype, root=None, props=None):
        if root is None:
            root = self.si.content.rootFolder
        container = self.si.content.viewManager.CreateContainerView(root, vimtype, True)
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
        if type(props) != list:
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

    def create_allocation_object(self, resSpec, value):
        result = vim.ResourceAllocationInfo()
        result.shares = vim.SharesInfo()
        result.shares.shares = value
        result.shares.level = vim.SharesInfo.Level.normal
        result.limit = -1
        result.reservation = 0
        result.expandableReservation = True
        return result

    def create_vapp(self, vapp_name, cluster_name, folder_name):
        content = self.si.content

        clusterMO = None

        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.ClusterComputeResource], True
        )

        for cluster in container.view:
            if cluster.name == cluster_name:
                clusterMO = cluster

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
        resSpec.scaleDescendantsShares = "disabled"
        resSpec.cpuAllocation = self.create_allocation_object(resSpec, 4000)
        configSpec = vim.vApp.VAppConfigSpec()
        configSpec.entityConfig = []
        configSpec.property = []

        clusterMO.resourcePool.CreateVApp(vapp_name, resSpec, configSpec, vmFolderMO)

    def delete_vapp(self, vapp_name):
        if vapp := self.get_vapp(vapp_name):
            if vapp.summary.vAppState != "stopped":
                # Wait for vApp PowerOff operation to complete
                task_id = vapp.PowerOffVApp_Task(True)
                task.WaitForTask(task_id)

            # Wait for vApp Destroy operation to complete
            task_id = vapp.Destroy_Task()
            task.WaitForTask(task_id)

    def poweroff_vapp(self, vapp_name):
        if vapp := self.get_vapp(vapp_name):
            if vapp.summary.vAppState != "stopped":
                # Wait for vApp PowerOff operation to complete
                task_id = vapp.PowerOffVApp_Task(True)
                task.WaitForTask(task_id)

    def poweron_vapp(self, vapp_name):
        if vapp := self.get_vapp(vapp_name):
            if vapp.summary.vAppState != "started":
                # We don't need to wait here
                # That means an instance was explictly powered off by a user
                # restart will go through all vms in that vApp anyway.
                vapp.PowerOnVApp_Task(True)

    def get_vapps(self, props=None):
        return self.get_obj_list([vim.VirtualApp], props=props)

    def get_vapp(self, name, props=None):
        return self.get_obj(vim.VirtualApp, "name", name, props=props)

    def get_vms(self, props=None):
        return self.get_obj_list([vim.VirtualMachine], props=props)

    def get_vm(self, name, props=None):
        return self.get_obj(vim.VirtualMachine, "name", name, props=props)

    def poweron_vm(self, vm_name):
        vm = self.get_vm(vm_name)
        task_id = vm.PowerOnVM_Task()
        task.WaitForTask(task_id)

    def set_vm_vcpu(self, vm_name, vcpu_num):
        # sourcery skip: class-extract-method
        # Fetch VM
        # For this example:
        # zbox.{instance_name}.{domain}
        vm = self.get_vm(vm_name)
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

    def set_vm_vmem(self, vm_name, vmem_gb):
        vm = self.get_vm(vm_name)
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

    def add_disk_to_vm(self, vm_name, disk_size_in_kb):
        #
        # Method to add a disk to a vm_name with specific disk_size_in_kb
        #

        # Fetch VM
        # For this example:
        # zbox.{instance_name}.{domain}
        vm = self.get_vm(vm_name)

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
        start_at = datetime.datetime.now()
        timeout = datetime.timedelta(seconds=timeout)

        print("Waiting for VMware Tools...")
        while start_at + timeout > datetime.datetime.now():
            vm = self.get_vm(vm_name)

            if vm.guest.toolsRunningStatus == "guestToolsRunning":
                return True
            print("Sleeping ...")
            time.sleep(5)

        if not tools_running:
            print("VMware Tools not running and timeout exceeded !")
            return False

    def wait_for_tools_ip(self, vm_name, ipaddress, timeout=120):
        start_at = datetime.datetime.now()
        timeout = datetime.timedelta(seconds=timeout)

        # We first need to wait for vmware tools to be ready
        status = self.wait_for_tools(vm_name)
        if not status:
            return False

        print("Waiting for VMware Tools IP...")
        while start_at + timeout > datetime.datetime.now():
            vm = self.get_vm(vm_name)

            if vm.guest.ipAddress == ipaddress:
                print(f"IP {ipaddress} found.")
                return True

            print("Sleeping...")
            time.sleep(5)

        if not ipaddress:
            return False

    @classmethod
    def auth_by_endpoint(cls, endpoint: M.Endpoint, **kwargs):
        compute = endpoint.endpoints["compute"]
        return cls(
            host=compute["hostname"],
            user=compute["username"],
            pwd=compute["password"],
            **kwargs,
        )

    @classmethod
    def auth_by_endpoint_id(cls, endpoint_id: int, **kwargs):
        with database.get_session_ctx() as session:
            endpoint = session.get(M.Endpoint, endpoint_id)
            return cls.auth_by_endpoint(endpoint, **kwargs)

    @classmethod
    def auth_by_instance(cls, instance: M.Instance, **kwargs):
        return cls.auth_by_endpoint(instance.endpoint, **kwargs)

    @classmethod
    def auth_by_instance_id(cls, instance_id: int, **kwargs):
        with database.get_session_ctx() as session:
            instance = session.get(M.Instance, instance_id)
            return cls.auth_by_instance(instance, **kwargs)
