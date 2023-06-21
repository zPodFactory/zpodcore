from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.vmware import vCenter
from zpodengine.instance_component_add.instance_component_add_utils import (
    handle_instance_component_add_failure,
)
from zpodengine.lib import database


@task
@handle_instance_component_add_failure
def instance_component_add_post_scripts(*, instance_component_id: int):
    with database.get_session_ctx() as session:
        instance_component = session.get(M.InstanceComponent, instance_component_id)
        custom_postscripts = instance_component.data.get("postscripts", [])
        print(f"Run Postscripts: {custom_postscripts}")

        c = instance_component.component
        print(c)

        # Specific behavior for critical instance components
        match c.component_name:
            case "zbox":
                print("--- zbox ---")
                # Add static routes on NSX T1 unless using vyos below

            case "vyos":
                print("--- vyos ---")
                # Add static routes on NSX T1
                # Potentially move DNS and other facilities to this later on

            case "vcsa":
                print("--- vcsa ---")
                # post-configure vcsa & add esxi, vcenter structure, etc.

            case "esxi":
                print("--- esxi ---")
                # Wait for vcsa to be deployed if not using vcsa-cli-installer (ova only)

            case _:
                print("Normal component, nothing to do here yet...")
