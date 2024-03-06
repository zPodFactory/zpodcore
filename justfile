set dotenv-load
set positional-arguments

# This calculates the number of columns for rich to aligne with docker-compose logs
# 16 is the length of the longest container name
# 3 is the length of the docker-compose padding
rich_cols := `echo $(tput cols) - $(echo ${COMPOSE_PROJECT_NAME:-zpodcore} | wc -c) - 17 - 3 | bc`

@_default:
  just --list --list-heading $'Commands:\n'

# Run alembic command in zpodapi container
alembic *args:
  docker compose exec -t zpodapi bash -c 'cd /zpodcore/scripts/alembic && alembic {{args}}'

# Upgrade database schema to head
alembic-upgrade rev="head":
  docker compose exec -t zpodapi bash -c "cd /zpodcore/scripts/alembic && alembic upgrade {{rev}}"

# Downgrade database schema -1
alembic-downgrade rev="-1":
  docker compose exec -t zpodapi bash -c "cd /zpodcore/scripts/alembic && alembic downgrade {{rev}}"

# Generate alembic revision
alembic-revision message='update':
  docker compose exec -t zpodapi bash -c "cd /zpodcore/scripts/alembic && alembic revision --autogenerate -m'{{message}}' && chown `id -u`:`id -g` --recursive /zpodcore/scripts/alembic/versions"

# Run zcli command
[no-exit-message]
zcli *args:
  @poetry -C zpodcli run zcli "$@"

zpod-release version:
  #!/usr/bin/env bash
  set -euo pipefail

  cd {{justfile_directory()}}
  if [[ `git status --porcelain` ]]; then
    # Dirty repo
    echo 'Uncommited changes in repo.  Commit or remove changes before creating release.'
    exit
  fi

  # Clean repo, so do the release
  poetry version {{version}}
  newversion=$(poetry version -s)
  git commit -am"Version v${newversion}"
  git push
  gh release create v${newversion} --generate-notes
  cd {{justfile_directory()}}/zpodsdk
  poetry build
  poetry publish

  cd {{justfile_directory()}}/zpodcli
  sed -i'' -e 's/zpodsdk = {/#zpodsdk = {/' pyproject.toml
  sed -i'' -e 's/#zpodsdk = "/zpodsdk = "/' pyproject.toml
  poetry build
  poetry publish
  sed -i'' -e 's/#zpodsdk = {/zpodsdk = {/' pyproject.toml
  sed -i'' -e 's/zpodsdk = "/#zpodsdk = "/' pyproject.toml

zpod-update version:
  #!/usr/bin/env bash
  set -euo pipefail

  if [[ `git status --porcelain` ]]; then
    echo 'Uncommited changes in repo.  Commit or remove changes before updating.'
    exit
  fi

  cd {{justfile_directory()}}
  cd /home/kvalenti/dev/zpodcore

  git fetch origin tag v{{version}} --no-tags
  git checkout tags/v{{version}}
  docker compose build
  docker compose down
  docker compose up -d
  just zpodengine-deploy-all

# Generate coverage docs
zpodapi-coverage:
  docker compose exec -t zpodapi bash -c "pytest --cov-report term-missing:skip-covered --cov-report html:tests/cov_html --cov zpodapi --cov zpodcommon && chown `id -u`:`id -g` --recursive /zpodcore/tests/cov_html"

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

# Start Docker Environment
zpodcore-start $COLUMNS=rich_cols:
  docker compose up --remove-orphans

# Start Docker Environment in background
zpodcore-start-background $COLUMNS=rich_cols:
  docker compose up -d --remove-orphans

# Stop Docker Environment
zpodcore-stop:
  docker compose down

# Deploy all Flows
zpodengine-deploy-all:
  just zpodengine-prefect --no-prompt deploy --all

# Manually Run Command
zpodengine-cmd *args:
  @cd {{justfile_directory()}}/zpodengine && PREFECT_API_URL="http://${ZPODENGINE_HOSTPORT}/api" PYTHONPATH="{{justfile_directory()}}/zpodcommon/src:{{justfile_directory()}}/zpodengine/src" poetry -C zpodengine run "$@"


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
    --rm -it ${COMPOSE_PROJECT_NAME:-zpodcore}-zpodengine:v1 bash

# Manually Run Prefect Command
zpodengine-prefect *args:
  just zpodengine-cmd prefect "$@"

# Update zpodsdk
zpodsdk-update: zpodapi-generate-openapi
  docker build -t zpodfactory/zpodsdk_builder zpodsdk_builder
  docker run -v "{{justfile_directory()}}/zpodsdk:/zpodcore/zpodsdk" zpodfactory/zpodsdk_builder bash -c "./update.sh && chown `id -u`:`id -g` --recursive /zpodcore/zpodsdk/zpod"
