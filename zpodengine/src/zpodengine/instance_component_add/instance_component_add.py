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
from zpodengine.lib.options import task_options_setup


def instance_component_add(
    *,
    instance_id: int,
    instance_name: str,
    component_uid: str,
    data=None,
    wait_for=None,
):  # sourcery skip: remove-unnecessary-cast
    prefix = f"{instance_name} {component_uid}"
    options = task_options_setup(prefix=prefix)

    instance_component_id = instance_component_add_prep.with_options(
        **options(name="prep"),
    ).submit(
        instance_id=instance_id,
        component_uid=component_uid,
        data=data or {},
        wait_for=wait_for,
    )

    pre_scripts = instance_component_add_pre_scripts.with_options(
        **options(name="prescripts"),
    ).submit(
        instance_component_id=instance_component_id,
        wait_for=[instance_component_id],
    )

    deploy = instance_component_add_deploy.with_options(
        **options(name="deploy"),
    ).submit(
        instance_component_id=instance_component_id,
        wait_for=[pre_scripts],
    )

    post_scripts = instance_component_add_post_scripts.with_options(
        **options(name="postscripts"),
    ).submit(
        instance_component_id=instance_component_id,
        wait_for=[deploy],
    )

    return instance_component_add_finalize.with_options(
        **options(name="finalize"),
    ).submit(
        instance_component_id=instance_component_id,
        wait_for=[post_scripts],
    )
