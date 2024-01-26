from zpodengine.instance_component_add.instance_component_add_1_prep import (
    instance_component_add_prep,
)
from zpodengine.instance_component_add.instance_component_add_2_pre_scripts import (
    instance_component_add_pre_scripts,
)
from zpodengine.instance_component_add.instance_component_add_3_deploy import (
    instance_component_add_deploy,
)
from zpodengine.instance_component_add.instance_component_add_4_post_scripts import (
    instance_component_add_post_scripts,
)
from zpodengine.instance_component_add.instance_component_add_5_finalize import (
    instance_component_add_finalize,
)
from zpodengine.lib.options import task_options_setup


def instance_component_add(
    *,
    instance_id: int,
    instance_name: str,
    component_uid: str,
    host_id: int | None = None,
    hostname: str | None = None,
    vcpu: int | None = None,
    vmem: int | None = None,
    vdisks: list[int] | None = None,
    wait_for=None,
):
    prefix = f"{instance_name} {component_uid}"
    options = task_options_setup(prefix=prefix)
    instance_component = instance_component_add_prep.with_options(
        **options(name="prep"),
    ).submit(
        instance_id=instance_id,
        component_uid=component_uid,
        host_id=host_id,
        hostname=hostname,
        wait_for=wait_for,
    )
    options = task_options_setup(
        prefix=f"{prefix} ({instance_component.result().hostname})"
    )

    pre_scripts = instance_component_add_pre_scripts.with_options(
        **options(name="prescripts"),
    ).submit(
        instance_component_id=instance_component.result().id,
        wait_for=[instance_component],
    )

    deploy = instance_component_add_deploy.with_options(
        **options(name="deploy"),
    ).submit(
        instance_component_id=instance_component.result().id,
        vcpu=vcpu,
        vmem=vmem,
        vdisks=vdisks,
        wait_for=[pre_scripts],
    )

    post_scripts = instance_component_add_post_scripts.with_options(
        **options(name="postscripts"),
    ).submit(
        instance_component_id=instance_component.result().id,
        wait_for=[deploy],
    )

    return instance_component_add_finalize.with_options(
        **options(name="finalize"),
    ).submit(
        instance_component_id=instance_component.result().id,
        wait_for=[post_scripts],
    )
