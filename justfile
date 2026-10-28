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

# Dump the whole database to ./zpodcore-db-<UTC timestamp>.sql (holds secrets)
zpodcore-db-dump:
  #!/usr/bin/env bash
  set -euo pipefail
  db="${ZPODCORE_POSTGRES_DSN##*/}"
  docker compose exec -T zpodpostgres pg_isready -q -h 127.0.0.1 -U postgres -d "$db" 2>/dev/null \
    || { echo "zpodpostgres is not running: start it with docker compose up -d zpodpostgres" >&2; exit 1; }
  file="zpodcore-db-$(date -u +%Y%m%dT%H%M%SZ).sql"
  # Written aside first, so a failed dump never leaves a file that looks complete.
  docker compose exec -T zpodpostgres pg_dump -U postgres -d "$db" > "$file.partial"
  mv "$file.partial" "$file"
  chmod 600 "$file"
  echo "$file ($(du -h "$file" | cut -f1)): restore it with just zpodcore-db-restore $file"

# Replace the database with a dump from zpodcore-db-dump (asks first, dumps the current one)
zpodcore-db-restore file:
  #!/usr/bin/env bash
  set -euo pipefail
  file="$1"
  db="${ZPODCORE_POSTGRES_DSN##*/}"
  [ -s "$file" ] || { echo "$file: no such dump" >&2; exit 1; }
  grep -q '^-- PostgreSQL database dump complete' "$file" \
    || { echo "$file is incomplete: pg_dump did not finish writing it" >&2; exit 1; }
  # The schema revision is the row right after the alembic_version COPY header.
  dumped="$(awk 'f { print; exit } /^COPY public.alembic_version /{ f = 1 }' "$file")"
  head="$(cd zpodapi/scripts/alembic/versions && python3 -c 'import re, sys
  revs, downs = set(), set()
  for f in sys.argv[1:]:
      t = open(f).read()
      revs |= set(re.findall(r"^revision = \"(\w+)\"", t, re.M))
      downs |= set(re.findall(r"^down_revision = \"(\w+)\"", t, re.M))
  print(" ".join(sorted(revs - downs)))' *.py)"
  echo "Dump schema: ${dumped:-unknown}; this checkout needs: $head"
  echo "This replaces the whole '$db' database. zpodapi and the zPod Engine stop."
  read -r -p "Type the database name ($db) to go on: " answer
  [ "$answer" = "$db" ] || { echo "Nothing changed." >&2; exit 1; }
  # The database may be stopped with the rest of the stack: start it, wait until it answers.
  docker compose up -d zpodpostgres
  for i in $(seq 1 30); do
    docker compose exec -T zpodpostgres pg_isready -q -h 127.0.0.1 -U postgres -d "$db" 2>/dev/null && break
    [ "$i" = 30 ] && { echo "zpodpostgres did not answer: nothing changed" >&2; exit 1; }
    sleep 2
  done
  just zpodcore-db-dump
  services="$(docker compose config --services | grep -vx zpodpostgres)"
  docker compose stop $services
  psql() { docker compose exec -T zpodpostgres psql -U postgres -v ON_ERROR_STOP=1 "$@"; }
  psql -q -d postgres -c "DROP DATABASE \"$db\" WITH (FORCE)" -c "CREATE DATABASE \"$db\""
  psql -q -d "$db" < "$file" > /dev/null
  echo "Restored $file. The stack is still stopped."
  if [ "$dumped" = "$head" ]; then
    echo "The dump matches this checkout: just zpodcore-start-background"
  else
    echo "The dump is at $dumped, not $head: go back to the code it was taken on"
    echo "(just zpod-update <git describe --tags noted then>). Starting this checkout"
    echo "would migrate it again."
  fi

# Run zcli command
[no-exit-message]
zcli *args:
  @uv --project zpodcli run zcli "$@"

# Cut a release: changelog heading, version markers, pretest, commit, tag, push (tools/README.md)
zpod-release version *args:
  python3 {{justfile_directory()}}/tools/release.py {{version}} --push {{args}}

# What a cut checks between releases: changelog, tags, tracked files, version markers
zpod-release-check:
  python3 {{justfile_directory()}}/tools/release.py --check
  python3 {{justfile_directory()}}/tools/version_markers.py --check

# Update the stack to main, a release (0.9.1) or any git ref (v0.9.0-2-g3f85190)
zpod-update target="main":
  #!/usr/bin/env bash
  set -euo pipefail
  cd {{justfile_directory()}}

  if [[ `git status --porcelain --untracked-files=no` ]]; then
    echo 'Uncommitted changes in repo. Commit or stash them before updating.' >&2
    exit 1
  fi

  target="{{target}}"
  current="$(git describe --tags 2>/dev/null || echo none)"
  cat <<EOF
  Updating zpodcore ${current} -> ${target}. To come back here: just zpod-update ${current}
  Read "Upgrading" in README.md first when crossing a minor version (0.7.x -> 0.8.x needs a
  database backup, a Prefect volume wipe and the zcore transition).
  EOF

  if [ "$target" = main ]; then
    git checkout main
    git pull --ff-only origin main
  elif [[ "$target" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    git fetch origin tag "v$target" --no-tags
    git checkout "tags/v$target"
  else
    git fetch origin --tags
    git checkout "$target"
  fi
  docker compose build
  docker compose down
  docker compose up -d

  # The API answers with X-zPod-API once prestart (migrations, default settings) is done.
  api="http://localhost:${ZPODAPI_HOSTPORT:-8000}"
  for i in $(seq 1 60); do
    if curl -fsI "$api/" 2>/dev/null | grep -qi '^x-zpod-api:'; then break; fi
    [ "$i" = 60 ] && { echo "zpodapi did not come up at $api" >&2; exit 1; }
    sleep 2
  done
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

# Bundle the stack's logs into ./zpodcore-logs-<UTC timestamp>.tar.gz, for a support request (since: 24h, 2026-10-28, ...)
zpodcore-logs-dump since="":
  #!/usr/bin/env bash
  set -euo pipefail
  since="$1"
  name="zpodcore-logs-$(date -u +%Y%m%dT%H%M%SZ)"
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  mkdir "$tmp/$name"
  services="$(docker compose config --services)"
  for service in $services; do
    docker compose logs --no-color --timestamps ${since:+--since "$since"} "$service" \
      > "$tmp/$name/$service.log" 2>&1 || true
  done
  {
    echo "zpodcore $(git describe --tags 2>/dev/null || echo unknown), logs since: ${since:-the start}"
    git status --short
    echo
    docker compose ps -a
    echo
    docker version --format 'docker {{{{.Server.Version}}'
    docker compose version
  } > "$tmp/$name/stack.txt" 2>&1
  # Written aside first, so a failed run never leaves a file that looks complete.
  tar -czf "$name.tar.gz.partial" -C "$tmp" "$name"
  mv "$name.tar.gz.partial" "$name.tar.gz"
  chmod 600 "$name.tar.gz"
  echo "$name.tar.gz ($(du -h "$name.tar.gz" | cut -f1)): logs of $(wc -w <<<"$services") services."
  echo "Logs can hold tokens or passwords: check it before sharing it."

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
      openapi-python-client generate --overwrite \
        --path /zpodcore/zpodsdk_builder/openapi.json \
        --config /zpodcore/zpodsdk_builder/config.yaml \
        --custom-template-path=/zpodcore/zpodsdk_builder/templates && \
      rm -f /zpodcore/zpodsdk/src/.gitignore \
        /zpodcore/zpodsdk/src/README.md \
        /zpodcore/zpodsdk/src/pyproject.toml && \
      chown `id --user`:`id --group` \
        --recursive /zpodcore/zpodsdk/src/zpodsdk"
