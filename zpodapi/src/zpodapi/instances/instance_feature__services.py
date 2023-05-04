from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M


class InstanceFeatureService(ServiceBase):
    base_model: M.InstanceFeature = M.InstanceFeature
