#!/usr/bin/env bash
# What must hold before a zpodcore version is committed and tagged. Run by tools/release.py
# as TEST_COMMAND, after the version markers are rewritten and before the "Release X.Y.Z"
# commit: release.py does `git add -A` afterwards, so the lockfiles refreshed here land in
# the commit the tag points at. Runs on the workstation, from the repository root.
#
#   tools/release_pretest.sh          # everything (what a cut runs)
#   tools/release_pretest.sh --quick  # markers and scoped tags only, no uv, no tests
set -euo pipefail
cd "$(dirname "$0")/.."

say() { printf '✓ %s\n' "$*"; }
die() { printf '✗ %s\n' "$*" >&2; exit 1; }

# 1. Every version marker agrees with the API's __version__.
version="$(python3 tools/version_markers.py --check)" || die "version markers disagree"
say "all version markers read $version"

# 2. A stack version is above every package-scoped tag too, or the cut would try to
#    re-upload an existing zpodcli/zpodsdk version to PyPI.
for tag in $(git tag -l 'zpodcli-v*' 'zpodsdk-v*'); do
  scoped="${tag#*-v}"
  if [ "$(printf '%s\n%s\n' "$scoped" "$version" | sort -V | tail -1)" != "$version" ] || [ "$scoped" = "$version" ]; then
    die "$version is not above the scoped tag $tag"
  fi
done
say "above every scoped tag"

[ "${1:-}" = "--quick" ] && exit 0

# 3. The lockfiles follow the version fields. Every subproject's uv.lock records its own
#    version (zpodapi and zpodengine too, although they are `package = false`), and zpodcli's
#    also records the zpodsdk path source; `uv run --locked` below refuses a stale one.
for project in zpodsdk zpodcli zpodapi zpodengine; do
  ( cd "$project" && uv lock )
done
say "lockfiles refreshed"

# 4. The four suites, each in its own environment.
for project in zpodsdk zpodcli zpodapi zpodengine; do
  ( cd "$project" && uv run --locked pytest -q )
done
say "suites green"

# 5. The two wheels build, and the zpodcli wheel requires the SDK released beside it.
( cd zpodsdk && rm -rf dist && uv build -q )
( cd zpodcli && rm -rf dist && uv build -q )
want="Requires-Dist: zpodsdk~=${version}"
if ! unzip -p zpodcli/dist/zpodcli-*.whl '*/METADATA' | grep -qx "$want"; then
  die "the zpodcli wheel does not carry '$want'"
fi
say "wheels build; zpodcli requires zpodsdk~=$version"
