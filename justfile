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
  docker compose exec -t zpodapi bash -c "cd /zpodcore/scripts/alembic && alembic revision --autogenerate -m'{{message}}'"

# docker prune everything
docker-fullclean:
  docker system prune -af
  docker volume prune -f

zcli *args:
  @poetry -C zpodcli run zcli "$@"

# Generate coverage docs
zpodapi-coverage:
  docker compose exec -t zpodapi bash -c "pytest --cov-report term-missing:skip-covered --cov-report html:tests/cov_html --cov zpodapi --cov zpodcommon"

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
  docker compose up

# Start Docker Environment in background
zpodcore-start-background $COLUMNS=rich_cols:
  docker compose up -d

# Stop Docker Environment
zpodcore-stop:
  docker compose down

# Update zpodsdk
zpodsdk-update: zpodapi-generate-openapi
  docker build -t zpodfactory/zpodsdk_builder zpodsdk_builder
  docker run -v "$(pwd)/zpodsdk:/zpodcore/zpodsdk" zpodfactory/zpodsdk_builder bash -c "./update.sh"

# Build zpodengine image
zpodengine-build-docker-image *options:
  docker build --build-arg INSTALL_DEV=true --tag ${COMPOSE_PROJECT_NAME:-zpodcore}-zpodengine:v1 --target dev --file zpodengine/dockerfile {{options}} .

# Open zpodengine CLI
zpodengine-cli:
  docker compose run --rm zpodenginecli

# Deploy zpodengine Blocks
zpodengine-create-blocks:
  docker compose run --rm zpodenginecli -c /zpodcore/scripts/create_blocks.py

# Deploy zpodengine Flows
zpodengine-create-deployments:
  docker compose run --rm zpodenginecli -c /zpodcore/scripts/create_deployments.py

# zpodengine initial config
zpodengine-init:
  just zpodengine-build-docker-image
  docker compose run --rm zpodenginecli -c "/zpodcore/scripts/create_default_settings.sh && /zpodcore/scripts/create_blocks.py && /zpodcore/scripts/create_deployments.py"
