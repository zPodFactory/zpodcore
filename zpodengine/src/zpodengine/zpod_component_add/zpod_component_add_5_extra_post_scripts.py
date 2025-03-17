from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.dbutils import DBUtils
from zpodengine.lib import database
from zpodengine.zpod_component_add.zpod_component_add_utils import (
    handle_zpod_component_add_failure,
)


@task
@handle_zpod_component_add_failure
def zpod_component_add_extra_post_scripts(*, zpod_component_id: int):
    with database.get_session_ctx() as session:
        zpod_component = session.get(M.ZpodComponent, zpod_component_id)

        zpodfactory_host = DBUtils.get_setting_value("zpodfactory_host")

        component = zpod_component.component
        zpod = zpod_component.zpod

        print(f"--- {component.component_name} ---")
        # Import dynamically the extra post-script module if it exists
        try:
            module_name = f"zpodengine.zpod_component_add.extra_post_scripts.{component.component_name}_extra_post_script"
            module = __import__(module_name, fromlist=['execute_extra_post_scripts'])

            print(f"Executing extra post-scripts for {component.component_name}")
            module.execute_extra_post_scripts(
                zpod_component=zpod_component,
                zpod=zpod,
                component=component,
                zpodfactory_host=zpodfactory_host,
                session=session
            )
        except ImportError:
            print(f"No extra post-scripts found for {component.component_name}")
            pass
