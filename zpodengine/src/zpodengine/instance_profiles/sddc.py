from zpodengine.instance_component_add.instance_component_add import (
    instance_component_add,
)


def instance_profile_flow(
    instance_id,
    wait_for=None,
):
    zbox = instance_component_add(
        instance_id=instance_id, component_uid="zbox-11.6", wait_for=wait_for
    )
    esxis = [
        instance_component_add(
            instance_id=instance_id,
            component_uid="esxi-8.0.0b",
            extra_id=x,
            data=dict(last_octet=x),
            wait_for=[zbox],
        )
        for x in range(11, 14)
    ]
    vcsa = instance_component_add(
        instance_id=instance_id,
        component_uid="vcsa-8.0.0b",
        wait_for=[esxis],
    )
    return instance_component_add(
        instance_id=instance_id,
        component_uid="nsx-4.1.0.0",
        wait_for=[vcsa],
    )
