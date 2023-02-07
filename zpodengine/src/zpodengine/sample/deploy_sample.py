import time

from prefect import flow, task


@task
def deploy():
    time.sleep(2)
    print("Finished")


@flow(log_prints=True)
def deploy_sample():
    vcenter = deploy.with_options(name="deploy_vcenter").submit()
    esxi_futures = [
        deploy.with_options(name=f"deploy_esxi{i}").submit(wait_for=vcenter)
        for i in range(11, 16)
    ]
    deploy.with_options(name="deploy_nsxt").submit(
        wait_for=esxi_futures,
    )


if __name__ == "main":
    print(deploy_sample())
