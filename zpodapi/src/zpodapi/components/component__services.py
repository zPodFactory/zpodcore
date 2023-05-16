from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M
from zpodcommon.enums import ComponentStatus, ComponentDownloadStatus
from zpodcommon.lib.zpodengine_client import ZpodEngineClient


class ComponentService(ServiceBase):
    base_model: SQLModel = M.Component

    def enable(self, *, component: M.Component):
        if (
            component.download_status == ComponentDownloadStatus.COMPLETE
            and component.status == ComponentStatus.ACTIVE
        ):
            return component
        component.download_status = ComponentDownloadStatus.SCHEDULED
        self.crud.save(component)

        zpod_engine = ZpodEngineClient()
        zpod_engine.create_flow_run_by_name(
            flow_name="component_download",
            deployment_name="default",
            uid=component.component_uid,
        )
        return component

    def disable(self, *, component: M.Component):
        component.status = ComponentStatus.INACTIVE
        return self.crud.save(component)
