from zpodengine.instance_component_add.instance_component_add import (
    instance_component_add,
)


def instance_profile_flow(
    instance_id: int,
    instance_name: str,
    wait_for=None,
):
    zbox = instance_component_add(
        instance_id=instance_id,
        instance_name=instance_name,
        component_uid="zbox-11.7",
        wait_for=wait_for,
    )
    esxis = [
        instance_component_add(
            instance_id=instance_id,
            instance_name=instance_name,
            component_uid="esxi-8.0u1",
            data=dict(last_octet=x, vcpu=4, vmem=32),
            wait_for=[zbox],
        )
        for x in range(11, 13)
    ]
    return instance_component_add(
        instance_id=instance_id,
        instance_name=instance_name,
        component_uid="vcsa-8.0u1",
        wait_for=[esxis],
    )
