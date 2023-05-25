import os

from com.vmware.appliance.update_client import Pending
from com.vmware.vapi.std.errors_client import Error
from prefect import flow, get_run_logger, task

from zpodcommon.lib.vapi import VAPIClient


@task(task_run_name="parse VCenter Updates object")
def parse_vc_update_object(updates: list):
    return [
        {
            "version": update.version,
            "name": update.name,
            "description": {
                "id": update.description.id,
                "default_message": update.description.default_message,
                "args": update.description.args,
                "params": update.description.params,
                "localized": update.description.localized,
            },
            "severity": update.severity,
            "priority": update.priority,
            "release_date": update.release_date,
            "reboot_required": update.reboot_required,
            "category": update.update_type,
            "size": update.size,
        }
        for update in updates
    ]


@task(task_run_name="Get VCenter Updates")
def get_vcenter_updates():

    hostname = os.getenv("VCENTER_HOSTNAME")
    username = os.getenv("VCENTER_USERNAME")
    password = os.getenv("VCENTER_PASSWORD")

    print(os.environ)
    print(hostname, username, password)

    stub_config = VAPIClient(hostname=hostname, username=username, password=password)

    logger = get_run_logger()
    pending_client = Pending(stub_config)
    source_type = pending_client.SourceType.LOCAL_AND_ONLINE

    try:
        logger.info("Checking for VCenter updates", style="green")
        return pending_client.list(source_type)
    except Error as e:
        logger.info("No updates available", e)
        return []


@flow(name="maintenance_operations", log_prints=True)
def flow_maintenance_operations():
    updates = get_vcenter_updates()
    vc_parsed_updates = parse_vc_update_object(updates)
    print(vc_parsed_updates)


if __name__ == "__main__":
    flow_maintenance_operations()
