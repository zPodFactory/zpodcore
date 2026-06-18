#!/usr/bin/env bash
#
# zcore-transition.sh — switch all profiles from the legacy `zbox-*` core
# component to `zcore-13.5`, so every *new* zPod deploys `zcore`.
#
# For every profile whose first component (the core) is a `zbox-*`, it uses the
# standard zcli edit flow:
#     just zcli profile info <name> -j > <file>     # current profile json
#     # rewrite the first component zbox-<ver> -> zcore-13.5 (+ hostname)
#     just zcli profile update <name> -pf <file>
#
# Plus: resync the library and enable the zcore component first.
#
# Idempotent (profiles already on zcore are skipped); requires `jq`. The zpodapi
# stack must be UP (zcli is an HTTP client). Typical use, after upgrading:
#     just zpodcore-stop && git pull && just zpodcore-start-background
#     # wait for zpodapi to be healthy, then:
#     just zcore-transition                  # = bash misc/zcore-transition.sh
#
set -euo pipefail

ZCORE_UID="${ZCORE_UID:-zcore-13.5}"
LIBRARY="${LIBRARY:-default}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-3600}"   # max seconds to wait for the OVA download
WAIT_POLL="${WAIT_POLL:-15}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
zcli() {
  if command -v just >/dev/null 2>&1; then
    ( cd "$ROOT" && just zcli "$@" )
  else
    ( cd "$ROOT" && uv --project zpodcli run zcli "$@" )
  fi
}

command -v jq >/dev/null 2>&1 || { echo "ERROR: jq is required" >&2; exit 1; }

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
