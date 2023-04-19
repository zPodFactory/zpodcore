import json
import logging
import types
from functools import cached_property

import httpx
from rich import print

from zpodcommon import models as M
from zpodcommon.lib import database

logger = logging.getLogger(__name__)


def safejson(self: httpx.Response):
    if self.status_code == 404:
        return {}
    try:
        self.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error(self.text)
        raise e

    try:
        return self.json()
    except json.JSONDecodeError:
        return {}


def event_hook_request(request: httpx.Request):
    # Log Request
    print(
        f"REQUEST: {request.method.upper()} {request.url}\n"
        f"{request.content.decode()}"
    )


def event_hook_response(response: httpx.Response):
    # Add safejson to response
    response.safejson = types.MethodType(safejson, response)
    response.read()
    request = response.request

    # Log Response
    print(
        f"RESPONSE: {request.method.upper()} {request.url}\n"
        f"{response.status_code} {response.safejson()}"
    )


class Auth(httpx.Auth):
    token_name = "x-xsrf-token"

    def __init__(self, **auth_args: dict):
        self.auth_args = auth_args

    def sync_auth_flow(self, request: httpx.Request):
        self.update_request(request)
        logger.debug(f"{request.method} {request.url} - {request.headers}")
        response: httpx.Response = yield request

        if response.status_code == 401:
            del self.sync_auth_info
            self.update_request(request)
            yield request

    @cached_property
    def sync_auth_info(self):
        logger.debug(
            f"POST {self.auth_args.get('url')} - {self.auth_args.get('headers')}"
        )
        response = httpx.post(**self.auth_args)
        if response.status_code != 200:
            raise ValueError(response.json())
        return response.headers.get(self.token_name), response.cookies

    def update_request(self, request: httpx.Request):
        token, cookies = self.sync_auth_info
        request.headers[self.token_name] = token
        httpx.Cookies(cookies).set_cookie_header(request)


class NsxClient(httpx.Client):
    def __init__(
        self,
        nsx_url: str,
        username: str,
        password: str,
        verify: bool = False,
        **kwargs,
    ):
        kwargs.setdefault("event_hooks", {})
        kwargs["event_hooks"].setdefault("request", []).insert(0, event_hook_request)
        kwargs["event_hooks"].setdefault("response", []).insert(0, event_hook_response)

        return super().__init__(
            auth=Auth(
                url=(f"{nsx_url}/api/session/create"),
                data=dict(j_username=username, j_password=password),
                timeout=httpx.Timeout(30.0, connect=60.0),
                verify=verify,
            ),
            base_url=f"{nsx_url}/policy/api",
            timeout=httpx.Timeout(30.0, connect=60.0),
            verify=verify,
            **kwargs,
        )

    @classmethod
    def by_endpoint_network(cls, epnet: dict, **kwargs):
        return cls(
            nsx_url=f"https://{epnet['hostname']}",
            username=epnet["username"],
            password=epnet["password"],
            **kwargs,
        )

    @classmethod
    def by_endpoint_id(cls, endpoint_id: int, **kwargs):
        with database.get_session_ctx() as session:
            endpoint = session.get(M.Endpoint, endpoint_id)
            epnet = endpoint.endpoints["network"]
        return cls.by_endpoint_network(epnet, **kwargs)

    @classmethod
    def by_instance(cls, instance: M.Instance, **kwargs):
        epnet = instance.endpoint.endpoints["network"]
        return cls.by_endpoint_network(epnet, **kwargs)


if __name__ == "__main__":
    nsx = NsxClient.by_endpoint_id(endpoint_id=1)
    x = nsx.get(url="/v1/infra/segments")
    print([x["display_name"] for x in x.safejson()["results"]])
