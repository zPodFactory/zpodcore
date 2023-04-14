import json
import logging
import typing

import httpx

logger = logging.getLogger(__name__)


class ZpodEngineBase:
    def _check_status(self, response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(response.text)
            raise e

    def _json(self, response) -> typing.Any:
        self._check_status(response)
        try:
            return response.json()
        except json.JSONDecodeError:
            return {}


class ZpodEngineClientAsync(ZpodEngineBase):
    def __init__(self):
        self.aclient = httpx.AsyncClient(
            base_url="http://zpodengineserver:4200/api",
        )

    async def __aenter__(self):
        await self.aclient.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type=None,
        exc_value=None,
        traceback=None,
    ):
        await self.aclient.__aexit__(exc_type, exc_value, traceback)

    async def get_deployment(self, flow_name, deployment_name):
        response = await self.aclient.get(
            url=f"/deployments/name/{flow_name}/{deployment_name}"
        )
        return self._json(response)

    async def get_deployment_id(self, flow_name, deployment_name):
        data = await self.get_deployment(flow_name, deployment_name)
        return data.get("id")

    async def create_flow_run(
        self,
        deployment_id,
        *,
        run_name=None,
        **parameters,
    ):
        response = await self.aclient.post(
            url=f"/deployments/{deployment_id}/create_flow_run",
            json={
                "name": run_name,
                "state": {"type": "SCHEDULED"},
                "parameters": parameters,
            },
        )
        return self._json(response)

    async def create_flow_run_by_name(
        self,
        flow_name,
        deployment_name,
        *,
        run_name=None,
        **parameters,
    ):
        deployment_id = await self.get_deployment_id(
            flow_name=flow_name,
            deployment_name=deployment_name,
        )
        return await self.create_flow_run(
            deployment_id=deployment_id,
            run_name=run_name,
            **parameters,
        )


class ZpodEngineClient(ZpodEngineBase):
    def __init__(self):
        self.client = httpx.Client(
            base_url="http://zpodengineserver:4200/api",
        )

    def __enter__(self):
        self.client.__enter__()
        return self

    def __exit__(
        self,
        exc_type=None,
        exc_value=None,
        traceback=None,
    ):
        self.client.__exit__(exc_type, exc_value, traceback)

    def get_deployment(self, flow_name, deployment_name):
        response = self.client.get(
            url=f"/deployments/name/{flow_name}/{deployment_name}"
        )
        return self._json(response)

    def get_deployment_id(self, flow_name, deployment_name):
        data = self.get_deployment(flow_name, deployment_name)
        return data.get("id")

    def create_flow_run(
        self,
        deployment_id,
        *,
        run_name=None,
        **parameters,
    ):
        response = self.client.post(
            url=f"/deployments/{deployment_id}/create_flow_run",
            json={
                "name": run_name,
                "state": {"type": "SCHEDULED"},
                "parameters": parameters,
            },
        )
        return self._json(response)

    def create_flow_run_by_name(
        self,
        flow_name,
        deployment_name="default",
        *,
        run_name=None,
        **parameters,
    ):
        deployment_id = self.get_deployment_id(
            flow_name=flow_name,
            deployment_name=deployment_name,
        )
        return self.create_flow_run(
            deployment_id=deployment_id,
            run_name=run_name,
            **parameters,
        )


def main():
    with ZpodEngineClient() as zpodengine:
        print(
            zpodengine.create_flow_run_by_name(
                flow_name="deploy-sample",
                deployment_name="deploy_sample",
            )
        )


if __name__ == "__main__":
    main()
