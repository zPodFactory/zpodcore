@_default:
  just --list

# Run alembic command in zpodapi container
alembic *args:
  docker exec -t zpodapi bash -c 'cd /zpodcore/scripts/alembic && alembic {{args}}'

# Upgrade database schema to head
alembic-upgrade rev="head":
  docker exec -t zpodapi bash -c "cd /zpodcore/scripts/alembic && alembic upgrade {{rev}}"

# Downgrade database schema -1
alembic-downgrade rev="-1":
  docker exec -t zpodapi bash -c "cd /zpodcore/scripts/alembic && alembic downgrade {{rev}}"

# Generate alembic revision
alembic-revision message='update':
  docker exec -t zpodapi bash -c "cd /zpodcore/scripts/alembic && alembic revision --autogenerate -m'{{message}}'"

# docker prune everything
docker-fullclean:
  docker system prune -af
  docker volume prune -f

# Generate coverage docs
zpodapi-coverage:
  docker exec -t zpodapi bash -c "pytest --cov-report term-missing:skip-covered --cov-report html:tests/cov_html --cov zpodapi --cov zpodcommon"

# Generate openapi json
zpodapi-generate-openapi:
  docker exec -t zpodapi python scripts/openapi/generate_openapi_json.py
  mv -vf scripts/openapi/openapi.json zpodsdk_builder/openapi.json

# Connect to zpodapi container and run command
zpodapi-exec *args="bash":
  docker exec -it zpodapi {{args}}

# Run pytest in zpodapi
zpodapi-pytest *args:
  docker exec -t zpodapi pytest {{args}}

# Start Docker Environment
zpodcore-start:
  docker compose up

# Stop Docker Environment
zpodcore-stop:
  docker compose down


# Update zpodsdk
zpodsdk-update: zpodapi-generate-openapi
  docker build -t zpodfactory/zpodsdk_builder zpodsdk_builder
  docker run -v "$(pwd)/zpodsdk:/zpodcore/zpodsdk" zpodfactory/zpodsdk_builder bash -c "./update.sh"

# Build zpodengine image
zpodengine-build-docker-image:
  docker build --build-arg INSTALL_DEV=true --tag zpodengine:v1 --target dev --file zpodengine/dockerfile .

# Open zpodengine CLI
zpodengine-cli:
  docker-compose run --rm zpodenginecli

# Deploy zpodengine Blocks
zpodengine-create-blocks:
  docker-compose run --rm zpodenginecli -c /zpodcore/scripts/create_blocks.py

# Deploy zpodengine Flows
zpodengine-create-deployments:
  docker-compose run --rm zpodenginecli -c /zpodcore/scripts/create_deployments.py

# zpodengine initial config
zpodengine-init:
  just zpodengine-build-docker-image
  docker-compose run --rm zpodenginecli -c "/zpodcore/scripts/create_blocks.py && /zpodcore/scripts/create_deployments.py"
