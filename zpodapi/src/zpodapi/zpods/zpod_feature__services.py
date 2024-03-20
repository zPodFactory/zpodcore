from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M


class ZpodFeatureService(ServiceBase):
    base_model: M.ZpodFeature = M.ZpodFeature
