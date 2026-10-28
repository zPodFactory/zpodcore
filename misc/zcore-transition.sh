#!/usr/bin/env bash
#
# zcore-transition.sh — rebuild the stack, then switch all profiles from the
# legacy `zbox-*` core component to `zcore-13.7`, so every *new* zPod deploys
# `zcore`.
#
# Run it after `git pull`, from the repo root (`just zcore-transition`). In order:
#   1. stop the stack, rebuild the images without cache, start it in the
#      background and wait for zpodapi and the Prefect server to answer;
#   2. re-register every flow (`just zpodengine-deploy-all`);
#   3. resync the library, enable the zcore component and wait for it to be ACTIVE;
#   4. for every profile whose first component (the core) is a `zbox-*`, the
#      standard zcli edit flow:
#        just zcli profile info <name> -j > <file>     # current profile json
#        # rewrite the first component zbox-<ver> -> zcore-13.7 (+ hostname)
#        just zcli profile update <name> -pf <file>
#
# Steps 3 and 4 against a stack that was not rebuilt and redeployed break things,
# hence 1 and 2 first. SKIP_REBUILD=1 skips 1 and 2 (a re-run on a stack already
# rebuilt). Idempotent (profiles already on zcore are skipped); requires `jq`,
# `curl` and `just`.
#
set -euo pipefail

ZCORE_UID="${ZCORE_UID:-zcore-13.7}"
LIBRARY="${LIBRARY:-default}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-3600}"   # max seconds to wait for the OVA download
WAIT_POLL="${WAIT_POLL:-15}"
STACK_TIMEOUT="${STACK_TIMEOUT:-600}"  # max seconds to wait for the stack to answer
SKIP_REBUILD="${SKIP_REBUILD:-0}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
zcli() { ( cd "$ROOT" && just zcli "$@" ); }

for tool in jq curl just; do
  command -v "${tool}" >/dev/null 2>&1 || { echo "ERROR: ${tool} is required" >&2; exit 1; }
done

# HOST:PORT from .env (just loads it); 0.0.0.0 means the local host.
local_url() { echo "http://${1/0.0.0.0/127.0.0.1}$2"; }
API_URL="$(local_url "${ZPODAPI_HOSTPORT:-0.0.0.0:8000}" /openapi.json)"
PREFECT_URL="$(local_url "${ZPODENGINE_ADMIN_HOSTPORT:-127.0.0.1:8061}" /api/health)"

wait_for() {  # wait_for <name> <url>
  local deadline=$(( SECONDS + STACK_TIMEOUT ))
  until curl -fsS -m 5 -o /dev/null "$2" 2>/dev/null; do
    if [ "${SECONDS}" -ge "${deadline}" ]; then
      echo "ERROR: $1 did not answer at $2 within ${STACK_TIMEOUT}s." >&2
      exit 1
    fi
    echo "    $1 not up yet, waiting ${WAIT_POLL}s..."
    sleep "${WAIT_POLL}"
  done
  echo "    $1 is up."
}

if [ "${SKIP_REBUILD}" != "1" ]; then
  echo "==> Stopping the stack..."
  ( cd "$ROOT" && just zpodcore-stop )

  echo "==> Rebuilding the images without cache..."
  ( cd "$ROOT" && docker compose build --no-cache )

  echo "==> Starting the stack in the background..."
  ( cd "$ROOT" && just zpodcore-start-background )

  echo "==> Waiting for zpodapi and the Prefect server..."
  wait_for zpodapi "${API_URL}"
  wait_for "Prefect server" "${PREFECT_URL}"

  echo "==> Re-registering every flow..."
  ( cd "$ROOT" && just zpodengine-deploy-all )
else
  echo "==> SKIP_REBUILD=1: using the running stack."
  wait_for zpodapi "${API_URL}"
fi

echo "==> Resyncing library '${LIBRARY}' (fetches '${ZCORE_UID}')..."
zcli library resync "${LIBRARY}"

echo "==> Enabling component '${ZCORE_UID}'..."
if ! zcli component enable "${ZCORE_UID}"; then
  echo "ERROR: could not enable '${ZCORE_UID}'. Is it present in library" \
       "'${LIBRARY}' after resync? Aborting." >&2
  exit 1
fi

# Enable only schedules the download; the component flips to ACTIVE once the OVA
# is downloaded and verified. Wait for that before rewriting profiles (profile
# validation also requires the component to be ACTIVE).
echo "==> Waiting for '${ZCORE_UID}' to become ACTIVE (downloading the OVA)..."
deadline=$(( SECONDS + WAIT_TIMEOUT ))
while :; do
  status="$(zcli component list -j 2>/dev/null \
    | jq -r --arg uid "${ZCORE_UID}" '.[] | select(.component_uid == $uid) | .status' \
    | head -n1)"
  if [ "${status}" = "ACTIVE" ]; then
    echo "    '${ZCORE_UID}' is ACTIVE."
    break
  fi
  if [ "${SECONDS}" -ge "${deadline}" ]; then
    echo "ERROR: timed out after ${WAIT_TIMEOUT}s waiting for '${ZCORE_UID}' to" \
         "become ACTIVE (last status: '${status:-<none>}')." >&2
    exit 1
  fi
  echo "    status='${status:-<none>}', waiting ${WAIT_POLL}s..."
  sleep "${WAIT_POLL}"
done

echo "==> Migrating profiles ('zbox-*' first component -> '${ZCORE_UID}')..."
mapfile -t profiles < <(zcli profile list -j 2>/dev/null | jq -r '.[].name')

if [ "${#profiles[@]}" -eq 0 ]; then
  echo "No profiles found."
  exit 0
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "${tmpdir}"' EXIT

changed=0
for name in "${profiles[@]}"; do
  [ -n "${name}" ] || continue
  f="${tmpdir}/${name}.json"

  if ! zcli profile info "${name}" -j > "${f}" 2>/dev/null; then
    echo "    - ${name}: 'profile info' failed, skipping"
    continue
  fi

  # The core component is the first element of the profile.
  if ! jq -e '(.[0].component_uid // "") | startswith("zbox-")' "${f}" >/dev/null; then
    echo "    - ${name}: first component is not zbox, skipping"
    continue
  fi

  jq --arg uid "${ZCORE_UID}" '
    .[0].component_uid = $uid
    | (if .[0].hostname == "zbox" then .[0].hostname = "zcore" else . end)
  ' "${f}" > "${f}.new" && mv "${f}.new" "${f}"

  zcli profile update "${name}" -pf "${f}"
  echo "    - ${name}: updated -> ${ZCORE_UID}"
  changed=$((changed + 1))
done

echo "==> Done. ${changed} profile(s) migrated to '${ZCORE_UID}'."
echo "    New zPods will now deploy '${ZCORE_UID}'. Existing zPods are unchanged."
