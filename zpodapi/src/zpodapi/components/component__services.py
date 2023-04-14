from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M
from zpodcommon.enums import ComponentStatus as CS
from zpodcommon.lib.zpodengine_client import ZpodEngineClient


class ComponentService(ServiceBase):
    base_model: SQLModel = M.Component

    def enable(self, *, component: M.Component):
        if component.status == CS.DOWNLOAD_COMPLETE and component.enabled is True:
            return component
        component.enabled = True
        component.status = CS.SCHEDULED
        self.crud.save(component)

        zpod_engine = ZpodEngineClient()
        zpod_engine.create_flow_run_by_name(
            flow_name="flow-download-component",
            deployment_name="default",
            uid=component.component_uid,
        )
        return component

    def disable(self, *, component: M.Component):
        component.enabled = False
        return self.crud.save(component)
