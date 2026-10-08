# zpodsdk

A Python client for the [zPodFactory](https://zpodfactory.github.io) zPod API, generated from
the API's OpenAPI document with [openapi-python-client](https://github.com/openapi-generators/openapi-python-client).
`zpodsdk` carries the version of the API it was generated from: use the SDK whose `major.minor`
matches your zPod API (`zpodsdk 0.8.x` for API `0.8.x`).

```
uv add zpodsdk          # or: pip install zpodsdk
```

Python 3.14 or newer.

## Usage

The API authenticates with an `access_token` header. `ZpodClient` wraps the generated client
and exposes one attribute per operation:

```python
from zpodsdk.zpod_client import ZpodClient

zpod = ZpodClient(
    base_url="https://zpodfactory.example.com:8000",
    headers={"access_token": "your-api-token"},
)

for z in zpod.zpods_get_all.sync():
    print(z.name, z.status)

detail = zpod.zpods_get.sync_detailed(id="name=my-zpod")
print(detail.status_code, detail.parsed)
```

Every operation has four callables: `sync` (parsed result, or `None`), `sync_detailed` (a
`Response` with `status_code`, `headers`, `content` and `parsed`), and their `asyncio` and
`asyncio_detailed` counterparts. Path and query parameters and request bodies are keyword
arguments; request and response models live in `zpodsdk.models`.

The generated `Client` and `AuthenticatedClient` are available too, for callers that prefer the
plain generated modules under `zpodsdk.api.<tag>`:

```python
from zpodsdk import Client
from zpodsdk.api.zpods import zpods_get_all

client = Client(base_url="https://zpodfactory.example.com:8000", headers={"access_token": "your-api-token"})
zpods = zpods_get_all.ZpodsGetAll(client).sync()
```

Certificate verification is on by default; pass `verify_ssl="/path/to/bundle.pem"` or, for a
lab you control, `verify_ssl=False` to the client.

`raise_on_unexpected_status` is `True` in `ZpodClient`: a status the OpenAPI document does not
declare raises `zpodsdk.errors.UnexpectedStatus` instead of returning `None`.

## Regenerating

The source of truth is the running API. From the repository root, with the dev stack up:

```
just zpodsdk-update
```

That exports `openapi.json` from the API container, runs `openapi-python-client` in the
`zpodsdk_builder` image with the templates and `config.yaml` there, and rewrites
`src/zpodsdk/`. This README and `pyproject.toml` are not generated; edit them by hand.

## Releasing

`zpodsdk` is released from the zpodcore monorepo together with the API, the engine and `zcli`:
one tag, one version, published to PyPI by the release workflow. See `tools/README.md` at the
repository root. Nothing here is published by hand.
