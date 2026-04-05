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
| `zpodsdk/` | Generated API client | `>=3.8.1` | PyPI |
| `zpodcli/` | `zcli` Typer CLI (depends on `zpodsdk`) | `>=3.10` | PyPI |
| `zpodapi/` | FastAPI service | `==3.12.1` | Docker |
| `zpodengine/` | Prefect flows | `==3.12.1` | Docker |
| `zpodsdk_builder/` | Regenerates `zpodsdk` from OpenAPI spec | `>=3.10,<3.13` | Docker (internal tool) |
| `zpodcommon/` | Shared source tree — **no** `pyproject.toml`, consumed via `PYTHONPATH` | n/a | — |

There is **no uv workspace**: each subproject locks and releases independently. The
root `pyproject.toml` only holds ruff config and the `[tool.bumpversion]` table used
by `just zpod-release`.

### Version bumping and releases

`just zpod-release <version>` uses [`bump-my-version`](https://github.com/callowayproject/bump-my-version)
(invoked via `uvx`, no install needed) to update the version string across all
subproject `pyproject.toml` + `__init__.py` files in a single commit + tag, then
runs `uv build` / `uv publish` for `zpodsdk` and `zpodcli`. The old `sed` dance that
toggled `zpodcli`'s `zpodsdk` dep between a path dependency and a pinned version is
gone — `[tool.uv.sources]` handles the dev path override, and `uv build` ignores
those sources so published wheels pin `zpodsdk==<version>` from PyPI automatically.

## POETRY → UV MIGRATION NOTES

The monorepo moved from Poetry to [uv](https://docs.astral.sh/uv/) in a single branch.
A few things worth knowing if you are resuming a branch older than the migration or
troubleshooting an unexpected pin:

- **Local `uv sync` for `zpodapi` / `zpodengine` requires `libpq-dev` on the host**
  because those projects pin `psycopg2` (source-only). If you only want the lockfile
  without building, run `uv lock`; full installs still happen inside the Docker
  builder stage which installs `libpq-dev` before `uv sync`.
- **`zpodsdk_builder` now pins `click<8.2`.** This was masked by `poetry.lock` (which
  had `click 8.1.8`). `openapi-python-client 0.20.0` via `typer <0.13` is incompatible
  with `click 8.2+` (`TypeError: Secondary flag is not valid for non-boolean flag`).
  Bump `openapi-python-client` itself if/when dropping this pin.
- **Dev path dep on `zpodsdk` is now in `zpodcli/pyproject.toml` under
  `[tool.uv.sources]`**, not in `[project.dependencies]`. Do not re-add a `path=`
  entry to the main dependency list — it would be embedded in the published wheel.
- **Build backend is `hatchling`** for the two publishable projects (`zpodsdk`,
  `zpodcli`). `zpodapi`, `zpodengine`, and `zpodsdk_builder` are all
  `[tool.uv] package = false` — they have no build target because their source is
  either bind-mounted in dev or `COPY`'d into the Docker image in prod.
- **Dockerfiles no longer set `POETRY_VENV` / `POETRY_VERSION`.** They now pull
  `uv` from `ghcr.io/astral-sh/uv:0.10` and write to `/opt/venv` (kept at that
  path via `UV_PROJECT_ENVIRONMENT=/opt/venv` for operator familiarity).
- **`uv.lock` replaces `poetry.lock`.** Commit it. It is cross-platform and
  deterministic. If you see a `poetry.lock` reappear in a PR, it is stale.
