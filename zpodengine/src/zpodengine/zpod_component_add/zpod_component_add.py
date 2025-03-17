from zpodengine.lib.options import task_options_setup
from zpodengine.zpod_component_add.zpod_component_add_1_prep import (
    zpod_component_add_prep,
)
from zpodengine.zpod_component_add.zpod_component_add_2_pre_scripts import (
    zpod_component_add_pre_scripts,
)
from zpodengine.zpod_component_add.zpod_component_add_3_deploy import (
    zpod_component_add_deploy,
)
from zpodengine.zpod_component_add.zpod_component_add_4_post_scripts import (
    zpod_component_add_post_scripts,
)
from zpodengine.zpod_component_add.zpod_component_add_5_config_scripts import (
    zpod_component_add_config_scripts,
)
from zpodengine.zpod_component_add.zpod_component_add_6_finalize import (
    zpod_component_add_finalize,
)


def zpod_component_add(
    *,
    zpod_id: int,
    zpod_name: str,
    component_uid: str,
    host_id: int | None = None,
    hostname: str | None = None,
    vcpu: int | None = None,
    vmem: int | None = None,
    vdisks: list[int] | None = None,
    wait_for=None,
):
    prefix = f"{zpod_name} {component_uid}"
    options = task_options_setup(prefix=prefix)
    zpod_component = zpod_component_add_prep.with_options(
        **options(name="prep"),
    ).submit(
        zpod_id=zpod_id,
        component_uid=component_uid,
        host_id=host_id,
        hostname=hostname,
        wait_for=wait_for,
    )
    options = task_options_setup(
        prefix=f"{prefix} ({zpod_component.result().hostname})"
    )

    pre_scripts = zpod_component_add_pre_scripts.with_options(
        **options(name="prescripts"),
    ).submit(
        zpod_component_id=zpod_component.result().id,
        wait_for=[zpod_component],
    )

    deploy = zpod_component_add_deploy.with_options(
        **options(name="deploy"),
    ).submit(
        zpod_component_id=zpod_component.result().id,
        vcpu=vcpu,
        vmem=vmem,
        vdisks=vdisks,
        wait_for=[pre_scripts],
    )

    post_scripts = zpod_component_add_post_scripts.with_options(
        **options(name="postscripts"),
    ).submit(
        zpod_component_id=zpod_component.result().id,
        wait_for=[deploy],
    )

    config_scripts = zpod_component_add_config_scripts.with_options(
        **options(name="config_scripts"),
    ).submit(
        zpod_component_id=zpod_component.result().id,
        wait_for=[post_scripts],
    )

    return zpod_component_add_finalize.with_options(
        **options(name="finalize"),
    ).submit(
        zpod_component_id=zpod_component.result().id,
        wait_for=[config_scripts],
    )
