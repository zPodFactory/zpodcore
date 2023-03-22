from zpodengine.instance_component.instance_component_deploy import (
    instance_component_deploy,
)
from zpodengine.instance_component.instance_component_finalize import (
    instance_component_finalize,
)
from zpodengine.instance_component.instance_component_post_scripts import (
    instance_component_post_scripts,
)
from zpodengine.instance_component.instance_component_pre_scripts import (
    instance_component_pre_scripts,
)
from zpodengine.instance_component.instance_component_prep import (
    instance_component_prep,
)


def add_instance_component(
    instance_id: int,
    component_uid: str,
    extra_id: str = "",
    data=None,
    wait_for=None,
):
    label = component_uid
    instance_component = instance_component_prep.submit(
        instance_id=instance_id,
        component_uid=component_uid,
        extra_id=extra_id,
        data=data or {},
        label=label,
        wait_for=wait_for,
    )
    pre_scripts = instance_component_pre_scripts.submit(
        instance_component=instance_component,
        label=label,
        wait_for=[instance_component],
    )
    package = instance_component_deploy.submit(
        instance_component=instance_component,
        label=label,
        wait_for=[pre_scripts],
    )
    post_scripts = instance_component_post_scripts.submit(
        instance_component=instance_component,
        label=label,
        wait_for=[package],
    )
    return instance_component_finalize.submit(
        instance_component=instance_component,
        label=label,
        wait_for=[post_scripts],
    )
