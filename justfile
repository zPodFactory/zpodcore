@_default:
  just --list

# Run pytest in zpodapi
zpodapi-pytest *args:
  docker exec -t zpodapi pytest {{args}}

# Generate coverage docs
zpodapi-coverage:
  pytest --cov-report term-missing:skip-covered --cov-report html:zpodapi/cov_html --cov zpodapi

# Connect to zpodapi container and run command
zpodapi-exec *args="bash":
  docker exec -it zpodapi {{args}}

# Start Docker Environment
zpodapi-start:
  docker-compose up

# Stop Docker Environment
zpodapi-stop:
  docker-compose down

# Run alembic command in zpodapi container
alembic *args:
  docker exec -t zpodapi bash -c 'cd /zpodcore/zpodapi/scripts/alembic && alembic {{args}}'

# Upgrade database schema to head
alembic-upgrade rev="head":
  docker exec -t zpodapi bash -c "cd /zpodcore/zpodapi/scripts/alembic && alembic upgrade {{rev}}"

# Downgrade database schema -1
alembic-downgrade rev="head":
  docker exec -t zpodapi bash -c "cd /zpodcore/zpodapi/scripts/alembic && alembic downgrade {{rev}}"

# Generate alembic revision
alembic-revision message='update':
  docker exec -t zpodapi bash -c "cd /zpodcore/zpodapi/scripts/alembic && alembic revision --autogenerate -m'{message}'"
