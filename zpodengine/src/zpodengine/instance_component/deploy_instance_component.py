import time
from typing import Any

from prefect import flow, task

from zpodcommon import models as M
from zpodengine.lib import database

sleep = 1


@task(task_run_name="{label}: prep")
def instance_component_prep(
    instance_id: int,
    component_uid: str,
    extra_key: str,
    data: dict[str, Any],
    label: str,
):
    with database.get_session_ctx() as session:
        instance = session.get(
            M.Instance,
            instance_id,
        )
        instance.components.append(
            M.InstanceComponent(
                component_uid=component_uid,
                extra_key=extra_key,
                data=data,
            )
        )

        session.add(instance)
        session.commit()
        session.refresh(instance)
        # data = instance.dict()
        # data["endpoint"] = instance.endpoint.dict()
        # data["components"] = [x.dict() for x in instance.components]
        # data["networks"] = [x.dict() for x in instance.networks]
        # data["permissions"] = [x.dict() for x in instance.permissions]
        # return data


@task(task_run_name="{label}: execute pre_scripts")
def instance_component_pre_scripts(
    instance_id: int,
    component_uid: str,
    extra_key: str,
    label: str,
):
    with database.get_session_ctx() as session:
        instance_component = session.get(
            M.InstanceComponent,
            dict(
                instance_id=instance_id,
                component_uid=component_uid,
                extra_key=str(extra_key or ''),
            ),
        )

    print(f"Run Prescripts: {instance_component.data.get('prescripts',[])}")


@task(task_run_name="{label}: deploy")
def instance_component_deploy(
    instance_id: int,
    component_uid: str,
    extra_key: str,
    label: str,
):
    print("Deploy OVA")


@task(task_run_name="{label}: execute post_scripts")
def instance_component_post_scripts(
    instance_id: int,
    component_uid: str,
    extra_key: str,
    label: str,
):
    with database.get_session_ctx() as session:
        instance_component = session.get(
            M.InstanceComponent,
            dict(
                instance_id=instance_id,
                component_uid=component_uid,
                extra_key=str(extra_key or ''),
            ),
        )

    print(f"Run Postscripts: {instance_component.data.get('postscripts',[])}")


@task(task_run_name="{label}: finalize")
def instance_component_finalize(
    instance_id: int,
    component_uid: str,
    extra_key: str,
    label: str,
):
    time.sleep(sleep)


def deploy_instance_component(
    instance_id: int,
    component_uid: str,
    extra_key: str = "",
    data=None,
    wait_for=None,
):
    label = component_uid
    prep = instance_component_prep.submit(
        instance_id=instance_id,
        component_uid=component_uid,
        extra_key=extra_key,
        data=data or {},
        label=label,
        wait_for=wait_for,
    )
    pre_scripts = instance_component_pre_scripts.submit(
        instance_id=instance_id,
        component_uid=component_uid,
        extra_key=extra_key,
        label=label,
        wait_for=[prep],
    )
    package = instance_component_deploy.submit(
        instance_id=instance_id,
        component_uid=component_uid,
        extra_key=extra_key,
        label=label,
        wait_for=[pre_scripts],
    )
    post_scripts = instance_component_post_scripts.submit(
        instance_id=instance_id,
        component_uid=component_uid,
        extra_key=extra_key,
        label=label,
        wait_for=[package],
    )
    return instance_component_finalize.submit(
        instance_id=instance_id,
        component_uid=component_uid,
        extra_key=extra_key,
        label=label,
        wait_for=[post_scripts],
    )


@flow(
    log_prints=True,
)
def deploy_component_flow(
    instance_id: int,
    component_uid: str,
):
    deploy_instance_component(instance_id=instance_id, component_uid=component_uid)


if __name__ == "__main__":
    print(deploy_component_flow(1, "cds-10.2"))
