import json
import logging
import types
from functools import cache, cached_property

import httpx

from zpodcommon import models as M
from zpodcommon.lib import database

logger = logging.getLogger(__name__)


def safejson(response: httpx.Response):
    if response.status_code == 404:
        return {}
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(response.text)
        raise e

    try:
        return response.json()
    except json.JSONDecodeError:
        return {}


def results(response: httpx.Response):
    return response.safejson().get("results", [])


def event_hook_request(request: httpx.Request):
    # Log Request
    print(
        f"REQUEST: {request.method.upper()} {request.url}\n"
        f"{request.content.decode()}"
    )


def event_hook_response(response: httpx.Response):
    # Add safejson to response
    response.safejson = types.MethodType(safejson, response)
    # Add results to response
    response.results = types.MethodType(results, response)

    response.read()
    request = response.request

    # Log Response
    print(
        f"RESPONSE: {request.method.upper()} {request.url}\n"
        f"{response.status_code} {response.safejson() or response.text}"
    )


def fmt(txt):
    escaped = txt.replace("/", "\\/")
    # Then URL encode only the backslashes, leaving the forward slashes as is
    newtxt = escaped.replace("\\", "%5C")
    return newtxt


class Auth(httpx.Auth):
    token_name = "x-xsrf-token"

    def __init__(self, **auth_args: dict):
        self.auth_args = auth_args

    def sync_auth_flow(self, request: httpx.Request):
        self.update_request(request)
        logger.debug(f"{request.method} {request.url} - {request.headers}")
        response: httpx.Response = yield request

        if response.status_code in (401, 403):
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
        host=None,
        user=None,
        pwd=None,
        verify: bool = False,
        **kwargs,
    ):
        kwargs.setdefault("event_hooks", {})
        kwargs["event_hooks"].setdefault("request", []).insert(0, event_hook_request)
        kwargs["event_hooks"].setdefault("response", []).insert(0, event_hook_response)

        nsx_url = f"https://{host}"
        print(f"Initializing NSX connection {nsx_url} with user {user}")
        return super().__init__(
            auth=Auth(
                url=(f"{nsx_url}/api/session/create"),
                data={
                    "j_username": user,
                    "j_password": pwd,
                },
                timeout=httpx.Timeout(30.0, connect=60.0),
                verify=verify,
            ),
            base_url=nsx_url,
            timeout=httpx.Timeout(30.0, connect=60.0),
            verify=verify,
            **kwargs,
        )

    @classmethod
    def auth_by_endpoint(cls, endpoint: M.Endpoint, **kwargs):
        epnet = endpoint.endpoints["network"]
        return cls(
            host=epnet["hostname"],
            user=epnet["username"],
            pwd=epnet["password"],
            **kwargs,
        )

    @classmethod
    def auth_by_endpoint_id(cls, endpoint_id: int, **kwargs):
        with database.get_session_ctx() as session:
            endpoint = session.get(M.Endpoint, endpoint_id)
            return cls.auth_by_endpoint(endpoint=endpoint, **kwargs)

    @classmethod
    def auth_by_zpod_endpoint(cls, zpod: M.Zpod, **kwargs):
        return cls.auth_by_endpoint(endpoint=zpod.endpoint, **kwargs)

    @classmethod
    def auth_by_zpod(cls, zpod: M.Zpod, **kwargs):
        return cls(
            host=f"nsx.{zpod.domain}",
            user="admin",
            pwd=zpod.password,
            **kwargs,
        )

    def search_one(self, **terms):
        if data := self.search(**terms):
            return data[0]
        raise ValueError("Item not found")

    def search_one_or_none(self, **terms):
        try:
            return self.search_one(**terms)
        except ValueError:
            return None

    def search(self, **terms):
        query = " AND ".join([f"{k}:{v}" for k, v in terms.items()])
        return self.get(url=f"/policy/api/v1/search/query?query={query}").results()

    @cache  # noqa: B019
    def edge_cluster_path(self, edge_cluster_name: str | None = None):
        edge_cluster_name = edge_cluster_name
        edge_cluster = self.search_one(
            resource_type="PolicyEdgeCluster",
            display_name=edge_cluster_name,
        )
        return edge_cluster.get("path", "")

    @cache  # noqa: B019
    def transport_zone_path(self, transport_zone_name: str | None = None):
        transport_zone_name = transport_zone_name
        transport_zone = self.search_one(
            resource_type="PolicyTransportZone",
            display_name=transport_zone_name,
        )
        return transport_zone.get("path", "")


if __name__ == "__main__":
    nsx = NsxClient.auth_by_endpoint_id(endpoint_id=1)
    x = nsx.get(url="/policy/api/v1/infra/segments")
    print([x["display_name"] for x in x.safejson()["results"]])
