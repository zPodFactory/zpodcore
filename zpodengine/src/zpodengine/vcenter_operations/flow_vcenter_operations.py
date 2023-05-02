import os

from prefect import flow, task

from zpodengine.vcenter_operations.vapi import VCenterOps


@task
def get_vcenter_updates():
    
    # TODO: will get these values from individual vapps.
    hostname = os.getenv("VCENTER_HOSTNAME")
    username = os.getenv("VCENTER_USERNAME")
    password = os.getenv("VCENTER_PASSWORD")

    vc = VCenterOps(hostname=hostname, username=username, password=password)

    updates = vc.get_vc_updates()
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


@flow(name="vcenter_operations", log_prints=True)
def flow_vcenter_operations():
    updates = get_vcenter_updates()
    print("Updates:\t", updates)


if __name__ == "__main__":
    flow_vcenter_operations()
