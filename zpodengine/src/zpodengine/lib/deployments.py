import importlib
import inspect

from prefect import Flow
from prefect.deployments import Deployment
from prefect.infrastructure import DockerContainer


def create_deployment(*, flow: str | Flow, **kwargs):
    """
        * flow=[module].[method_name]
          ex.
            flow="instance_deploy.flow_instance_deploy.flow_instance_deploy"
        * flow=[deployment_name]
          ex.
            flow="instance_deploy".  This is equal to "instance_deploy.flow_instance_deploy.flow_instance_deploy".
        * flow=method
          ex.
            from zpodengine.instance_deploy.flow_instance_deploy import flow_instance_deploy
            flow=flow_instance_deploy
    """  # noqa: E501, B950

    def get_flow(flow_):
        if type(flow_) == str:
            if "." not in flow_:
                flow_ = f"{flow_}.flow_{flow_}.flow_{flow_}"
            module_name, method = flow_.rsplit(".", 1)
            mod = importlib.import_module(f"zpodengine.{module_name}")
            flow_method = getattr(mod, method)
            flow_filepath = getattr(mod, "__file__", None)
        else:
            flow_method = flow_
            flow_filepath = inspect.getfile(flow_.fn)
        return dict(
            flow=flow_method,
            entrypoint=f"{flow_filepath}:{flow_method.fn.__name__}",
        )

    data = (
        dict(
            apply=True,
            infrastructure=DockerContainer.load("zpodengine"),
            name="default",
            path="/zpodcore/src/zpodengine",
            skip_upload=True,
            version=1,
            work_queue_name="default",
        )
        | get_flow(flow)
        | kwargs
    )
    result = Deployment.build_from_flow(**data)
    print(f"Created Deployment: {result.flow_name}/{result.name}")
    return result
