from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.vcsadeployer import vcsa_extract_iso, vcsa_fix_permissions
from zpodengine.instance_component_add.instance_component_add_utils import (
    handle_instance_component_add_failure,
)
from zpodengine.lib import database


@task
@handle_instance_component_add_failure
def instance_component_add_pre_scripts(*, instance_component_id: int):
    with database.get_session_ctx() as session:
        instance_component = session.get(M.InstanceComponent, instance_component_id)
        custom_prescripts = instance_component.data.get("prescripts", [])
        print(f"Run Prescripts: {custom_prescripts}")

        c = instance_component.component
        print(c)

        match c.component_name:
            case "vcsa":
                print("--- vcsa ---")

                # Extract component iso content
                vcsa_extract_iso(c)

                # Set execute permissions on required binaries
                vcsa_fix_permissions(c)
