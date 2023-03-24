from zpodengine.instance_component.instance_component import add_instance_component


def instance_profile_flow(
    instance_id,
    wait_for=None,
):
    zbox = add_instance_component(
        instance_id=instance_id, component_uid="zbox-11.6", wait_for=None
    )
    esxis = [
        add_instance_component(
            instance_id=instance_id,
            component_uid="esxi-8.0.0b",
            extra_id=x,
            data=dict(last_octet=x),
            wait_for=zbox,
        )
        for x in range(11, 14)
    ]
    vcsa = add_instance_component(
        instance_id=instance_id,
        component_uid="vcsa-8.0.0b",
        wait_for=[esxis],
    )
    add_instance_component(
        instance_id=instance_id,
        component_uid="nsx-4.1.0.0",
        wait_for=[vcsa],
    )
