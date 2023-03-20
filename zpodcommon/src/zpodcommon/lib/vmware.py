import atexit
import logging
import ssl

from pyVim import connect
from pyVmomi import vim, vmodl

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
            raise ConnectionError("Unable to connect to host.") from e

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

        ret = []
        for o in result.objects:
            item = {"obj": o.obj}
            for p in o.propSet:
                item[p.name] = p.val
            ret.append(item)
        return ret

    def get_vapps(self, props=None):
        return self.get_obj_list([vim.VirtualApp], props=props)

    def get_vapp(self, name, props=None):
        return self.get_obj(vim.VirtualApp, "name", name, props=props)

    def get_vms(self, props=None):
        return self.get_obj_list([vim.VirtualMachine], props=props)

    def get_vm(self, name, props=None):
        return self.get_obj(vim.VirtualMachine, "name", name, props=props)
