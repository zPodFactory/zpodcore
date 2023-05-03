from zpodengine.instance_component_add.instance_component_add_deploy import (
    instance_component_add_deploy,
)
from zpodengine.instance_component_add.instance_component_add_finalize import (
    instance_component_add_finalize,
)
from zpodengine.instance_component_add.instance_component_add_post_scripts import (
    instance_component_add_post_scripts,
)
from zpodengine.instance_component_add.instance_component_add_pre_scripts import (
    instance_component_add_pre_scripts,
)
from zpodengine.instance_component_add.instance_component_add_prep import (
    instance_component_add_prep,
)
from zpodengine.instance_component_add.instance_component_add_utils import (
    instance_component_add_failed,
)


def instance_component_add(
    instance_id: int,
    component_uid: str,
    extra_id: str = "",
    data=None,
    wait_for=None,
):  # sourcery skip: remove-unnecessary-cast
    keys = dict(
        instance_id=instance_id,
        component_uid=component_uid,
        extra_id=str(extra_id),
    )
    failed_func = instance_component_add_failed(keys)
    label = component_uid

    instance_component = instance_component_add_prep.with_options(
        on_failure=[failed_func]
    ).submit(
        keys=keys,
        data=data or {},
        label=label,
        wait_for=wait_for,
    )
    pre_scripts = instance_component_add_pre_scripts.with_options(
        on_failure=[failed_func]
    ).submit(
        keys=keys,
        label=label,
        wait_for=[instance_component],
    )
    package = instance_component_add_deploy.with_options(
        on_failure=[failed_func]
    ).submit(
        keys=keys,
        label=label,
        wait_for=[pre_scripts],
    )
    post_scripts = instance_component_add_post_scripts.with_options(
        on_failure=[failed_func]
    ).submit(
        keys=keys,
        label=label,
        wait_for=[package],
    )
    return instance_component_add_finalize.with_options(
        on_failure=[failed_func]
    ).submit(
        keys=keys,
        label=label,
        wait_for=[post_scripts],
    )
