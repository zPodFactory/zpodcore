import importlib

from prefect import flow


@flow(
    flow_run_name="deploy_{zpodname}",
    log_prints=True,
)
def deploy_zpod(
    profile: str,
    zpodname: str,
):
    mod = importlib.import_module(f"zpodengine.deploy.profiles.{profile}")
    mod.flow()


if __name__ == "__main__":
    print(deploy_zpod("zpod-awesome", "special"))
