from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M


class InstanceNetworkService(ServiceBase):
    base_model: M.InstanceNetwork = M.InstanceNetwork
