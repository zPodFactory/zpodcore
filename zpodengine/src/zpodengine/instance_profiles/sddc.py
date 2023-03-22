from zpodengine.instance_component.instance_component import add_instance_component


def instance_profile_flow(
    instance_id,
    wait_for=None,
):
    esxis = [
        add_instance_component(
            instance_id=instance_id,
            component_uid="esxi-8.0.0",
            extra_id=x,
            data=dict(last_octet=x),
            wait_for=wait_for,
        )
        for x in range(11, 14)
    ]
    vcsa = add_instance_component(
        instance_id=instance_id,
        component_uid="vcsa-8.0.0",
        wait_for=[esxis],
    )
    nsxt = add_instance_component(
        instance_id=instance_id,
        component_uid="nsxt-4.3.1",
        wait_for=[vcsa],
    )
    add_instance_component(
        instance_id=instance_id,
        component_uid="hcx-2.6.3",
        wait_for=[nsxt],
    )
