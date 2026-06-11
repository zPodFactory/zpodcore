import json
import logging
import time
import types
from functools import cache, cached_property

import httpx

from zpodcommon import models as M
from zpodcommon.lib import database

logger = logging.getLogger(__name__)


# HTTP statuses we treat as transient — typically what a saturated reverse
# proxy in front of NSX (or NSX while it's hammering vCenter) returns when
# it can't service the request right now.
RETRY_STATUS_CODES = frozenset({502, 503, 504})

# httpx exceptions that signal a transient network/protocol failure where
# another attempt has a real chance of succeeding. ConnectError /
# ConnectTimeout are already retried by httpx.HTTPTransport via its own
# `retries=` parameter, but we list them here too so the application-level
# loop catches any that escape (e.g. on the read side).
RETRY_HTTPX_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadError,
    httpx.ReadTimeout,
    httpx.RemoteProtocolError,
)


class RetryTransport(httpx.HTTPTransport):
    """``httpx.HTTPTransport`` that retries transient failures.

    The NSX manager sits behind a reverse proxy that occasionally returns
    ``502/503/504`` or an empty body when NSX or vCenter are under load.
    Connection-establishment retries are delegated to the parent class
    (``retries=`` parameter); on top of that this transport adds:

      * status-code retries for :data:`RETRY_STATUS_CODES`
      * exception retries for :data:`RETRY_HTTPX_EXCEPTIONS`
      * exponential backoff between attempts (``backoff * 2**attempt``)

    Applied to every NSX request — including the auth POST — so callers
    don't need their own retry decorators.
    """

    def __init__(
        self,
        *args,
        max_retries: int = 3,
        backoff: float = 0.5,
        **kwargs,
    ) -> None:
        super().__init__(*args, retries=max_retries, **kwargs)
        self._max_retries = max_retries
        self._backoff = backoff

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        for attempt in range(self._max_retries + 1):
            try:
                response = super().handle_request(request)
            except RETRY_HTTPX_EXCEPTIONS as exc:
                if attempt >= self._max_retries:
                    raise
                # print() rather than logger.warning so Prefect's
                # log_prints=True picks it up into the task-run logs.
                print(
                    f"NSX {request.method} {request.url} — "
                    f"{type(exc).__name__} "
                    f"(attempt {attempt + 1}/{self._max_retries + 1}), "
                    "retrying"
                )
                time.sleep(self._backoff * (2 ** attempt))
                continue
            if (
                response.status_code in RETRY_STATUS_CODES
                and attempt < self._max_retries
            ):
                print(
                    f"NSX {request.method} {request.url} — "
                    f"HTTP {response.status_code} "
                    f"(attempt {attempt + 1}/{self._max_retries + 1}), "
                    "retrying"
                )
                response.close()
                time.sleep(self._backoff * (2 ** attempt))
                continue
            return response
        # Loop body returns or raises on every path; this is just a safety
        # belt to satisfy static type checkers.
        raise RuntimeError("RetryTransport loop exited without returning")


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
        # A 2xx (typically 200) with a body that isn't valid JSON usually
        # means the NSX reverse proxy returned an HTML / empty page under
        # load. Swallow it as {} for backward compat, but log the status
        # code and a body snippet so the case is visible in Prefect logs
        # (log_prints=True captures print()) — if this fires regularly,
        # the next step is to retry it.
        body_preview = (response.text or "<empty body>")[:200]
        print(
            f"NSX safejson: {response.request.method} {response.request.url} "
            f"returned HTTP {response.status_code} with non-JSON body, "
            f"falling back to {{}} — body[:200]={body_preview!r}"
        )
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

    # Log Response
    print(
        f"RESPONSE: {response.status_code}\n"
        f"{response.text}"
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
        # Drive the auth POST through a Client backed by RetryTransport so
        # the login itself rides through transient 5xx / read errors from
        # the NSX reverse proxy — the original symptom this fix targets.
        post_args = {k: v for k, v in self.auth_args.items() if k != "verify"}
        verify = self.auth_args.get("verify", True)
        with httpx.Client(transport=RetryTransport(verify=verify)) as client:
            response = client.post(**post_args)
        # Surface the auth status code unconditionally — at the same level
        # as the "Initializing NSX connection" message that ran earlier in
        # NsxClient.__init__ — so operators can see exactly what HTTP
        # status NSX returned before any downstream call uses the token.
        # This is the symptom from the original JSONDecodeError traceback,
        # where the actual status was hidden by response.json() crashing.
        print(
            f"NSX auth POST {post_args.get('url')} -> "
            f"HTTP {response.status_code}"
        )
        if response.status_code != 200:
            # Use .text not .json(): a saturated reverse proxy returns an
            # HTML / empty body and json() would mask the real auth failure
            # with a JSONDecodeError.
            raise ValueError(
                f"NSX auth failed (HTTP {response.status_code}): "
                f"{response.text or '<empty body>'}"
            )
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
        # Every NSX request runs through RetryTransport so transient
        # 502/503/504 from the reverse proxy and read-side errors get
        # retried transparently to callers.
        kwargs.setdefault("transport", RetryTransport(verify=verify))

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
