set dotenv-load
set positional-arguments

# This calculates the number of columns for rich to aligne with docker-compose logs
# 16 is the length of the longest container name
# 3 is the length of the docker-compose padding
rich_cols := `echo $(tput cols) - $(echo ${COMPOSE_PROJECT_NAME:-zpodcore} | wc -c) - 17 - 3 | bc`

@_default:
  just --list  

# Run alembic command in zpodapi container
alembic *args:
  docker compose exec -t zpodapi bash -c "\
    cd /zpodcore/scripts/alembic && \
    alembic {{args}}"

# Downgrade database schema -1
alembic-downgrade rev="-1":
  docker compose exec -t zpodapi bash -c "\
    cd /zpodcore/scripts/alembic && \
    alembic downgrade {{rev}}"

# Generate alembic revision
alembic-revision message='update':
  docker compose exec -t zpodapi bash -c "\
    cd /zpodcore/scripts/alembic && \
    alembic revision --autogenerate -m'{{message}}' && \
    chown `id --user`:`id --group` \
      --recursive /zpodcore/scripts/alembic/versions"

# Upgrade database schema to head
alembic-upgrade rev="head":
  docker compose exec -t zpodapi bash -c "\
    cd /zpodcore/scripts/alembic && \
    alembic upgrade {{rev}}"

# Run zcli command
[no-exit-message]
zcli *args:
  @uv --project zpodcli run zcli "$@"

# Create a release version
zpod-release version:
  #!/usr/bin/env bash
  set -euo pipefail

  # Verify uv is installed
  if ! command -v uv >/dev/null 2>&1; then
      echo 'Install uv first: https://docs.astral.sh/uv/'
      exit 1
  fi

  # Verify gh is installed
  if ! command -v gh >/dev/null 2>&1; then
      echo 'Install gh first'
      exit 1
  fi

  # Verify user is logged into gh
  if ! gh auth status >/dev/null 2>&1; then
      echo 'You need to login: gh auth login'
      exit 1
  fi

  # Verify that repo is clean
  cd {{justfile_directory()}}
  if [[ `git status --porcelain` ]]; then
    # Dirty repo
    echo 'Uncommited changes in repo.  Commit or remove changes before creating release.'
    exit 1
  fi

  # Bump version across all subprojects + root (see [tool.bumpversion] in pyproject.toml).
  # bump-my-version commits and tags automatically.
  uvx bump-my-version bump --new-version {{version}} patch
  newversion={{version}}

  # Refresh zpodcli's lockfile so the new zpodsdk pin is reflected
  cd {{justfile_directory()}}/zpodcli
  uv lock --upgrade-package zpodsdk
  git commit -am "Update zpodcli/uv.lock for v${newversion}" || true

  git push
  git push --tags

  # Create github release
  gh release create v${newversion} --generate-notes

  # Build and publish zpodsdk (uv build reads PyPI creds from
  # UV_PUBLISH_TOKEN or ~/.pypirc; uv publish ignores [tool.uv.sources])
  cd {{justfile_directory()}}/zpodsdk
  uv build
  uv publish

  # Build and publish zpodcli. `uv build` ignores [tool.uv.sources], so the
  # wheel pins `zpodsdk==${newversion}` from PyPI — no sed dance needed.
  cd {{justfile_directory()}}/zpodcli
  uv build
  uv publish

# Update to a release version
zpod-update version:
  #!/usr/bin/env bash
  set -euo pipefail

  if [[ `git status --porcelain` ]]; then
    echo 'Uncommited changes in repo.  Commit or remove changes before updating.'
    exit
  fi

  cd {{justfile_directory()}}
  git fetch origin tag v{{version}} --no-tags
  git checkout tags/v{{version}}
  docker compose build
  docker compose down
  docker compose up -d
  sleep 10
  just zpodengine-deploy-all

# Generate coverage docs
zpodapi-coverage:
  docker compose exec -t zpodapi bash -c "\
    pytest \
      --cov-report term-missing:skip-covered \
      --cov-report html:tests/cov_html \
      --cov zpodapi \
      --cov zpodcommon && \
    chown `id --user`:`id --group` \
      --recursive /zpodcore/tests/cov_html"

# Generate openapi json
zpodapi-generate-openapi:
  docker compose exec -t zpodapi python scripts/openapi/generate_openapi_json.py
  mv -vf zpodapi/scripts/openapi/openapi.json zpodsdk_builder/openapi.json

# Connect to zpodapi container and run command
zpodapi-exec *args="bash":
  docker compose exec -it zpodapi {{args}}

# Run pytest in zpodapi
zpodapi-pytest *args:
  docker compose exec -t zpodapi pytest {{args}}

# Run all subproject unit tests locally (no docker)
zpod-runtests:
  #!/usr/bin/env bash
  set -uo pipefail
  cd {{justfile_directory()}}

  bold=$'\e[1m'
  cyan=$'\e[36m'
  green=$'\e[32m'
  red=$'\e[31m'
  dim=$'\e[2m'
  reset=$'\e[0m'

  declare -a SUBJECTS=(
    "zpodapi|zpodapi"
    "zpodcli|zpodcli"
    "zpodengine|zpodengine (+ zpodcommon)"
    "zpodsdk|zpodsdk"
  )

  # Aligns test ids to W cols (truncating long ones), counts results, prints
  # a one-line "N/M passed (P%) in Ts" summary at the end.
  format_results() {
    awk -v W=70 '
      BEGIN { passed=0; failed=0; skipped=0; duration="?" }
      /^[^[:space:]]+::[^[:space:]]+ (PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)/ {
        match($0, /PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS/)
        status = substr($0, RSTART, RLENGTH)
        nodeid = substr($0, 1, RSTART - 2)
        if (length(nodeid) > W) nodeid = substr(nodeid, 1, W - 3) "..."
        color = (status == "PASSED" || status == "XPASS") ? "\033[32m" \
              : (status == "SKIPPED" || status == "XFAIL") ? "\033[33m" \
              : "\033[31m"
        printf "  %-*s %s%s\033[0m\n", W, nodeid, color, status
        if (status == "PASSED" || status == "XPASS") passed++
        else if (status == "SKIPPED" || status == "XFAIL") skipped++
        else failed++
        next
      }
      /^=+ .* in [0-9.]+s/ {
        if (match($0, /in [0-9.]+s/)) {
          duration = substr($0, RSTART + 3, RLENGTH - 3)
        }
        next
      }
      END {
        total = passed + failed + skipped
        print ""
        if (total == 0) {
          print "  \033[33mno tests collected\033[0m"
        } else {
          rate = int(100 * passed / total + 0.5)
          color = failed ? "\033[31m" : "\033[32m"
          if (failed) {
            printf "  %s%d/%d passed (%d%%)\033[0m — %d failed — %s\n", \
                   color, passed, total, rate, failed, duration
          } else {
            printf "  %s%d/%d passed (%d%%)\033[0m in %s\n", \
                   color, passed, total, rate, duration
          }
        }
      }
    '
  }

  failed=()
  for entry in "${SUBJECTS[@]}"; do
    dir="${entry%%|*}"
    label="${entry##*|}"
    echo
    echo "${bold}${cyan}── ${label} ──${reset}"
    # Disable color in pytest output so awk filtering is easier; we add our own.
    # The stderr filter drops Python readline's "Cannot read termcap database"
    # warning, harmless on Debian where /etc/termcap (legacy) is not shipped.
    if ! { cd "$dir" && uv run --group dev pytest -v --no-header --color=no -p no:warnings 2> >(grep -vE 'Cannot read termcap|using dumb terminal' >&2); } | format_results; then
      failed+=("$label")
    fi
  done

  echo
  echo "${bold}── Summary ──${reset}"
  if [ ${#failed[@]} -eq 0 ]; then
    echo "${green}${bold}All subprojects passed${reset}"
  else
    echo "${red}${bold}Failed:${reset} ${failed[*]}"
    exit 1
  fi

# Start Docker Environment
zpodcore-start $COLUMNS=rich_cols:
  docker compose up --remove-orphans

# Start Docker Environment in background
zpodcore-start-background $COLUMNS=rich_cols:
  docker compose up -d --remove-orphans

# Stop Docker Environment
zpodcore-stop:
  docker compose down

# Migrate all profiles from zbox-* to the new zcore component
zcore-transition:
  @bash misc/zcore-transition.sh

# Deploy all Flows
zpodengine-deploy-all:
  just zpodengine-prefect --no-prompt deploy --all

# Manually Run Command
zpodengine-cmd *args:
  @cd {{justfile_directory()}}/zpodengine && PREFECT_API_URL="http://${ZPODENGINE_HOSTPORT}/api" PYTHONPATH="{{justfile_directory()}}/zpodcommon/src:{{justfile_directory()}}/zpodengine/src" uv run "$@"


# Run command using zpodengine container
zpodengine-run *args="bash":
  @docker run \
    --volume {{justfile_directory()}}/zpodcommon/src/zpodcommon:/zpodcore/src/zpodcommon \
    --volume {{justfile_directory()}}/zpodengine/src/zpodengine:/zpodcore/src/zpodengine \
    --volume {{justfile_directory()}}/zpodengine/scripts:/zpodengine/scripts \
    --volume {{justfile_directory()}}/.env:/zpodcore/.env \
    --volume $ZPODCORE_DNSMASQ_SERVERS_PATH:/zpod/dnsmasq_servers \
    --volume $ZPODCORE_LIBRARY_PATH:/library \
    --volume $ZPODCORE_PRODUCTS_PATH:/products \
    --volume $ZPODCORE_RESULTS_PATH:/results \
    --network "${COMPOSE_PROJECT_NAME:-zpodcore}_default" \
    --env PREFECT_API_URL="http://zpodengineserver:4200/api" \
    --env PREFECT_LOCAL_STORAGE_PATH="/results" \
    --rm -it ${COMPOSE_PROJECT_NAME:-zpodcore}-zpodengine:v1 "$@"

# Manually Run Prefect Command
zpodengine-prefect *args:
  just zpodengine-cmd prefect "$@"

# Update zpodsdk
zpodsdk-update: zpodapi-generate-openapi
  docker build -t zpodfactory/zpodsdk_builder zpodsdk_builder
  docker run \
    --volume "{{justfile_directory()}}/zpodsdk:/zpodcore/zpodsdk" \
    zpodfactory/zpodsdk_builder \
    bash -c "\
      cd /zpodcore && \
      openapi-python-client update \
        --path /zpodcore/zpodsdk_builder/openapi.json \
        --config /zpodcore/zpodsdk_builder/config.yaml \
        --custom-template-path=/zpodcore/zpodsdk_builder/templates && \
      chown `id --user`:`id --group` \
        --recursive /zpodcore/zpodsdk/src/zpodsdk"
