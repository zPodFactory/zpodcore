# Unit tests

Per-subproject inventory of the unit test baseline. Each test is light by
design — pure logic, smoke imports, or in-memory FastAPI exercises. Nothing
hits Postgres, Prefect, vCenter, NSX, or other live services.

## Running tests

Tests run from each subproject's directory using its own venv:

```bash
cd zpodapi      && uv run --group dev pytest
cd zpodcli      && uv run --group dev pytest
cd zpodengine   && uv run --group dev pytest   # also runs zpodcommon tests
cd zpodsdk      && uv run --group dev pytest
```

`zpodcommon` has no venv of its own, so its tests live in `zpodcommon/tests/`
and are picked up by `zpodengine`'s pytest config (`testpaths` in
`zpodengine/pyproject.toml`).

Total baseline: **56 tests** across the five subprojects.

---

## zpodapi — 42 tests

FastAPI app exercised via `fastapi.testclient.TestClient` against an
in-memory SQLite database. Conftest seeds two users (`superuser`, `normaluser`)
and exposes `superadmin_client` / `normaluser_client` fixtures.

### `tests/conftest.py`

Shared fixtures only — no test functions:
- `session` — SQLite in-memory engine, fresh schema per test.
- `client` — `TestClient` with `get_session` overridden to use the test session.
- `superadmin_client` / `normaluser_client` — `client` with appropriate `access_token` header pre-set.
- `db_seed` (autouse) — inserts the two seed users on every test.

### `tests/test_root.py`

| Test | What it checks |
|---|---|
| `test_root` | `GET /` returns 200 and the `X-zPod-API: true` header. |

### `tests/test_users.py`

| Test | What it checks |
|---|---|
| `test_bad_token` | Unknown token → 403. |
| `test_normaluser_create_user` | Non-admin POST `/users` → 403. |
| `test_superadmin_create_user` | Admin can create a user; response echoes input fields. |
| `test_superadmin_create_user_with_duplicated_username` | Duplicate username → 409. |
| `test_superadmin_get_users` | Admin sees all users. |
| `test_normaluser_get_users` | Normal user only sees themselves. |
| `test_superadmin_get_user_me` / `test_normaluser_get_user_me` | `/users/me` returns the caller. |
| `test_superadmin_get_user_by_username` | Lookup by username works. |
| `test_superadmin_get_user_by_email` | Lookup by email works. |
| `test_superadmin_get_user_username_not_found` / `test_superadmin_get_user_email_not_found` | Missing user → 404. |
| `test_superadmin_patch_user` / `test_normaluser_patch_user` | PATCH updates description. |
| `test_superadmin_patch_user_missing` | PATCH on missing id → 404. |
| `test_superadmin_disable_user_by_username` / `..._by_email` | Admin can disable users → 202. |
| `test_normaluser_disable_user_by_username` / `..._by_email` | Normal user cannot disable → 403. |
| `test_superadmin_disable_user_missing` | Disable on missing user → 404. |

`ignore()` helper strips volatile fields (`id`, `creation_date`, …) from
response payloads before equality checks.

### `tests/test_routes_smoke.py` — 21 tests (parametrized)

Smoke coverage for every top-level collection route besides `/users` (which
has its own dedicated file). Each path is exercised three ways via
`pytest.mark.parametrize`. Catches regressions where a schema fails to
import or serialize after a dependency upgrade.

Routes covered: `/components`, `/endpoints`, `/libraries`,
`/permission_groups`, `/profiles`, `/settings`, `/zpods`.

| Test | What it checks |
|---|---|
| `test_superadmin_get_collection_returns_list[<path>]` | Admin GET returns 200 + a list. |
| `test_collection_rejects_bad_token[<path>]` | Unknown token → 403. |
| `test_normaluser_get_collection_returns_list[<path>]` | Non-admin GET returns 200 (filtered) or 403 (e.g. `/settings` is admin-only). |

---

## zpodcli — 2 tests

Typer CLI exercised via `typer.testing.CliRunner`. No live API calls.

### `tests/test_smoke.py`

| Test | What it checks |
|---|---|
| `test_help` | `zcli --help` exits 0. Confirms the typer app, all subcommand groups, and their imports load cleanly. |
| `test_version` | `zcli --version` exits 0. Verifies the version callback wiring. |

---

## zpodengine — 2 tests

Prefect flows can't be unit-tested in isolation (they need a Prefect runtime),
so this is purely import smoke for the modules.

### `tests/test_smoke.py`

| Test | What it checks |
|---|---|
| `test_import_lib_modules` | `zpodengine.lib.{network, options, utils}` import without side effects. |
| `test_import_flow_modules` | `flow_component_download`, `flow_zpod_deploy`, `flow_zpod_destroy` import. Catches Prefect/SQLModel/pyvmomi compatibility regressions at import time. |

---

## zpodcommon — 7 tests

Pure-Python tests for shared models and helpers. Discovered by zpodengine's
pytest (no own venv).

### `tests/test_enums.py` — 5 tests

| Test | What it checks |
|---|---|
| `test_case_insensitive_lookup` | `EndpointComputeDrivers("vsphere"/"VSPHERE"/"VSphere")` all resolve to `VSPHERE`. Verifies the `CaseInsensitiveEnum._missing_` lookup path. |
| `test_component_status_values` | `ComponentStatus.ACTIVE.value == "ACTIVE"`. |
| `test_endpoint_status_values` | `EndpointStatus.ACTIVE.value == "ACTIVE"`. |
| `test_user_status_values` | `UserStatus.ENABLED` / `UserStatus.DISABLED` round-trip through `.value`. |
| `test_zpod_status_has_expected_states` | `ZpodStatus` exposes `"ACTIVE"`. |

### `tests/test_network_utils.py` — 2 tests

| Test | What it checks |
|---|---|
| `test_mgmt_ip_arithmetic` | `MgmtIp(10.0.0.0/24, host_id=1)` → `ip="10.0.0.1"`, `netmask="255.255.255.0"`, `prefixlen="24"`, `cidr="10.0.0.1/24"`. |
| `test_mgmt_ip_known_host_ids` | The `MGMT_HOST_IDS` map contains the expected entries (`gw=1`, `zbox=2`, `vcsa=10`, `nsxt=20`). Catches accidental edits to the contract used across deployments. |

---

## zpodsdk — 3 tests

Auto-generated by `openapi-python-client`, so deep tests aren't worthwhile —
the SDK reflects whatever the OpenAPI schema says. Smoke tests confirm the
package and a representative slice of generated classes import and instantiate.

### `tests/test_smoke.py`

| Test | What it checks |
|---|---|
| `test_client_instantiation` | `Client(base_url=...)` constructs. |
| `test_authenticated_client_instantiation` | `AuthenticatedClient(base_url=..., token=...)` constructs. |
| `test_user_create_model` | `UserCreate(username=..., email=...)` constructs and round-trips fields. |

---

## Coverage gaps to address later

These are deliberately *not* in the baseline; they each need infra or design
decisions before adding:

- **zpodapi**: list routes for all top-level collections are smoke-covered.
  Detailed CRUD tests still only exist for `/users`. POST/PATCH/DELETE on
  `/zpods`, `/endpoints`, `/libraries`, `/components`,
  `/permission_groups`, `/profiles`, `/settings` are untested.
- **zpodcli**: only `--help` / `--version`. No subcommand-level tests
  (would need an SDK-mocking fixture).
- **zpodengine**: no flow-level tests. Would need a Prefect test harness
  (`prefect_test_harness` fixture).
- **zpodcommon**: `lib/{vmware,nsx,zboxapi,zpodengine_client,dbutils}`,
  `models/*`, plus most enums, are untested.
- **zpodsdk**: per-endpoint API call tests would need an HTTP mock
  (e.g. `respx` against `httpx`).
