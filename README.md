# zPod Core

zPodFactory Core Engine

## DEVELOPMENT ENVIRONMENT SETUP

Complete the following steps to set up your development environment:

1. Install Docker and Docker Compose

1. Install [uv](https://docs.astral.sh/uv/):

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

    uv will manage the Python toolchain for you — no separate pyenv step is
    required. Each subproject pins its own `requires-python`, and
    `uv sync` will download the matching interpreter automatically.

1. Create each subproject virtualenv. In `/zpodapi`, `/zpodengine`, `/zpodcli`, and `/zpodsdk`, run:

    ```bash
    uv sync
    ```

    Each subproject is released independently and keeps its own `uv.lock`.

1. Configure Environment Variables.  (See `/zpodapi/src/zpodapi/lib/settings.py` file for all available settings)  In the root directory, run:

    ```bash
    cp .env.default .env
    vim .env
    ```

1. For Visual Studios Code, do the following:

    a. Configure the zpodcore.code-workspace.  In `/` run:

    ```bash
    cp zpodcore.code-workspace.default zpodcore.code-workspace
    ```

    Make sure that the port variable in launch.configurations.connect.port matches the port stored in the `ZPODAPI_DEBUG_HOSTPORT` environment variable.

1. Build the Docker containers.
In the root directory, run:

    ```bash
    docker compose build
    ```

1. Start the environment.  In the root directory, run:

    ```bash
    just zpodcore-start
    ```

1. Verify that zpodapi is working by opening a browser and going to `http://localhost:[8000 or ZPODAPI_HOSTPORT]` and `http://localhost:[8000 or ZPODAPI_HOSTPORT]/docs`

1. Create Deployments

    ```bash
    just zpodengine-deploy-all
    ```

## PACKAGE LAYOUT

The monorepo is split into independently-released subprojects, each with its own
`pyproject.toml` and `uv.lock`:

| Subproject | Role | Python | Released |
|---|---|---|---|
| `zpodsdk/` | Generated API client | `>=3.14` | PyPI, from the tag |
| `zpodcli/` | `zcli` Typer CLI (requires `zpodsdk~=<version>`) | `>=3.14` | PyPI, from the tag |
| `zpodapi/` | FastAPI service | `3.14` (image `python:3.14-slim-trixie`) | Docker, built from the checkout |
| `zpodengine/` | Prefect flows | `3.14` (image `prefecthq/prefect:3.x-python3.14`) | Docker, built from the checkout |
| `zpodsdk_builder/` | Regenerates `zpodsdk` from the OpenAPI document | `3.14` | Docker (internal tool) |
| `zpodcommon/` | Shared source tree — **no** `pyproject.toml`, consumed via `PYTHONPATH` | n/a | — |

There is **no uv workspace**: each subproject locks on its own. The root `pyproject.toml`
only holds ruff config.

### Versioning and releases

One version for four packages. A tag `vX.Y.Z` moves the zPod API, the zPod Engine, `zcli`
and `zpodsdk` together (nine version markers: four `__init__.py`, five `pyproject.toml`),
and the tag publishes `zpodsdk` then `zpodcli` to PyPI. The API decides the digit: minor
when the API changes shape (an endpoint, a schema, a permission), patch otherwise.
`zpodsdk` always carries the version of the API it was generated from. `zcli X.Y.*` is
built for API `X.Y.*` and requires `zpodsdk~=X.Y.Z`, so a zcli-only fix can ship on its
own later without an SDK upload; lockstep is the default.

| You run | Use | Why |
|---|---|---|
| zPod API 0.8.x | zcli 0.8.x, zpodsdk 0.8.x | same endpoints and schemas; patch digits may differ |
| zPod API 0.7.2 | zcli 0.7.2, zpodsdk 0.7.2 | zcli 0.8 calls endpoints 0.7.2 does not have |
| a mix | upgrade the stack first, then the CLI | the API tolerates an older CLI; the reverse is not true |

Cutting a release is one command, `just zpod-release X.Y.Z`, which runs
`python3 tools/release.py X.Y.Z --push`: the `[Unreleased]` section of `CHANGELOG.md`
becomes `[X.Y.Z]`, the nine markers and the `zpodsdk~=` requirement move, the lockfiles
are refreshed, the four test suites run, both wheels build, then one commit, the tag,
the push. GitHub publishes the changelog section as the release note and both packages to
PyPI. `tools/README.md` has the details, what stops a release, and the PyPI setup.
`just zpod-release-check` runs the between-releases rules locally; CI runs them on every
push.

### Upgrading from 0.7.x to 0.8.x

0.8.0 is the first release after two years. The upgrade is automatic where it can be;
these steps are not:

1. **Back up the database.** The one Alembic migration drops the `zpod_features` table
   (features now live as JSON on the zPod), and the Postgres image moved from bullseye to
   trixie, so the entrypoint reindexes every database on first start. Both run on their
   own; neither is reversible.
2. **Host toolchain**: uv replaces pyenv and Poetry. `just zcli` needs uv; a local
   `uv sync` of `zpodapi` or `zpodengine` needs `gcc` and `libpq-dev` for `psycopg2`.
3. **Prefect 2 → 3**: stop the stack, remove the Prefect volume, start, then
   `just zpodengine-deploy-all`. Flow-run history is lost; the deployments are re-registered.
4. **zbox → zcore**: once the API is up, `just zcore-transition` (needs `jq`). It resyncs
   the library, enables `zcore-13.5`, waits for it to be `ACTIVE` and rewrites every profile
   whose first component is `zbox-*`. Existing zPods are untouched.
5. **Broadcom downloads**: set the `zpodfactory_broadcom_download_token` setting; library
   entries still using the removed `customerconnect` or `avipulse` engines end in
   `FAILED_UNSUPPORTED_ENGINE` until their URL is changed.
6. **Optional**: set `compute.vds` on endpoints whose NSX transport zone spans several
   VDSs; enable `ff_nsx_clean_orphan_ports` only after reading one destroy log with it off;
   enable `ff_endpoint_ova_staging` per site.
7. **No `.env` change**: `.env.default` is identical to 0.7.2; new behaviour is driven by
   settings seeded at API start.

`just zpod-update X.Y.Z` fetches the tag, rebuilds and restarts the stack, waits for the
API and redeploys the flows; it prints which versions it crosses and points here.
PyPI users: `uv tool install zpodcli==X.Y.Z` (uv provisions Python 3.14).

### Tests

`just zpod-runtests` runs the four suites with a summary; or, per subproject,
`uv run pytest` in `zpodapi`, `zpodcli`, `zpodengine` (which also picks up
`zpodcommon/tests/`) and `zpodsdk`. Everything is light by design: `zpodapi` exercises the
FastAPI app with `TestClient` against in-memory SQLite (users CRUD, a smoke pass over every
collection route, FQDN validation); `zpodcli` checks `--help` and `--version`; `zpodengine`
is import smoke for the libraries and flows plus the NSX orphan-port classification;
`zpodcommon` covers enums and `MgmtIp`; `zpodsdk` instantiates the client and a model.
Nothing hits Postgres, Prefect, vCenter or NSX. CI runs the same four commands on every push.

## POETRY → UV MIGRATION NOTES

The monorepo moved from Poetry to [uv](https://docs.astral.sh/uv/) in a single branch.
A few things worth knowing if you are resuming a branch older than the migration or
troubleshooting an unexpected pin:

- **Local `uv sync` for `zpodapi` / `zpodengine` requires both `gcc` and `libpq-dev`
  on the host** because those projects pin `psycopg2` (source-only). psycopg2's
  `setup.py` shells out to `cc` and includes libpq headers. On Debian/Ubuntu:
  `sudo apt install gcc libpq-dev`. If you only want the lockfile without building,
  run `uv lock` instead of `uv sync` — resolution alone doesn't compile anything.
  Full installs still happen inside the Docker builder stages, which install both
  `libpq-dev` and `gcc` before `uv sync`.
- **`zpodsdk_builder` runs `openapi-python-client` 0.29** (the earlier `click<8.2`
  workaround for 0.20 is gone). `just zpodsdk-update` regenerates `zpodsdk/src/zpodsdk/`
  from the running API; `zpodsdk/README.md` and `zpodsdk/pyproject.toml` are hand-written.
- **Dev path dep on `zpodsdk` is in `zpodcli/pyproject.toml` under
  `[tool.uv.sources]`**, not in `[project.dependencies]`, which carries the
  `zpodsdk~=<version>` requirement the wheel ships. Do not re-add a `path=` entry to the
  main dependency list — it would be embedded in the published wheel.
- **Build backend is `hatchling`** for the two publishable projects (`zpodsdk`,
  `zpodcli`). `zpodapi`, `zpodengine`, and `zpodsdk_builder` are all
  `[tool.uv] package = false` — they have no build target because their source is
  either bind-mounted in dev or `COPY`'d into the Docker image in prod.
- **Dockerfiles no longer set `POETRY_VENV` / `POETRY_VERSION`.** They now pull
  `uv` from `ghcr.io/astral-sh/uv:0.12` and write to `/opt/venv` (kept at that
  path via `UV_PROJECT_ENVIRONMENT=/opt/venv` for operator familiarity).
- **`uv.lock` replaces `poetry.lock`.** Commit it. It is cross-platform and
  deterministic. If you see a `poetry.lock` reappear in a PR, it is stale.
