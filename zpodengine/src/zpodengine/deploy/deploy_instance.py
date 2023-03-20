import importlib

from prefect import flow


@flow(
    flow_run_name="deploy_{zpodname}",
    log_prints=True,
)
def deploy_zpod(
    profile: str,
    zpodname: str,
    instance_id: int,
):
    mod = importlib.import_module(f"zpodengine.deploy.profiles.{profile}")
    mod.flow(instance_id=instance_id)


if __name__ == "__main__":
    deploy_zpod(profile="sddc", zpodname="abc", instance_id=1)
