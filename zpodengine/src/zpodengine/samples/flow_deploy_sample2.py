import time

from prefect import flow, task


@task(task_run_name="deploy_{component_type}")
def deploy2(component_type):
    time.sleep(2)
    print("Finished")


@flow(flow_run_name="deploy_{zpodname}")
def flow_deploy_sample2(zpodname: str):
    vcenter = deploy2.submit("vcenter")
    esxi_futures = [deploy2.submit(f"esxi{i}", wait_for=vcenter) for i in range(11, 16)]
    deploy2.submit("nsxt", wait_for=esxi_futures)


if __name__ == "__main__":
    print(flow_deploy_sample2("zpod-awesome"))
