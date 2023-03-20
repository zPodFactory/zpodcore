from zpodengine.instance_component.deploy_instance_component import (
    deploy_instance_component,
)


def instance_profile_flow(
    instance_id,
    wait_for=None,
):
    esxis = [
        deploy_instance_component(instance_id, f"esxi-8.0.0 [{x}]", wait_for=wait_for)
        for x in range(11, 14)
    ]
    vcsa = deploy_instance_component(instance_id, "vcsa-8.0.0", wait_for=esxis)
    nsxt = deploy_instance_component(instance_id, "nsxt-4.3.1", wait_for=vcsa)
    deploy_instance_component(instance_id, "hcx-2.6.3", wait_for=nsxt)
