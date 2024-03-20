from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M


class ZpodNetworkService(ServiceBase):
    base_model: M.ZpodNetwork = M.ZpodNetwork
