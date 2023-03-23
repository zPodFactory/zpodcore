from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M


class InstanceFeatureService(ServiceBase):
    base_model: SQLModel = M.InstanceFeature
