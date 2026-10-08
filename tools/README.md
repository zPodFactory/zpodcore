# Releasing

Two scripts, standard library only, the same in every zPodFactory repository. What differs per
repository is the configuration block at the top of each one. zpodcore is a monorepo, so two
small helpers sit beside them.

| Script | Does |
|---|---|
| `release.py` | cuts a version: changelog heading, version bump in all nine markers, pretest, commit, tag, push. Also `--check` and `--draft`. |
| `release_notes.py` | turns a version's `CHANGELOG.md` section into the GitHub release note. Run by the workflow. |
| `release_pretest.sh` | what `release.py` runs before the commit: lockfiles, the four test suites, both wheels, the zpodcli → zpodsdk requirement. |
| `version_markers.py` | the nine places the version is written; `--check` fails if they disagree. CI runs it. |

## One version, four packages

A zpodcore release is a stack release: `vX.Y.Z` moves the API, the engine, `zcli` and
`zpodsdk` together, and the tag publishes `zpodsdk` then `zpodcli` to PyPI. The API decides the
digit: minor when the API changes shape (an endpoint, a schema, a permission), patch otherwise.
`zpodsdk` is generated from the API and always carries the API's version. `zpodcli` requires
`zpodsdk~=X.Y.Z`, so a zpodcli-only patch can ship on its own later (a package-scoped tag such
as `zpodcli-v0.8.1`; not wired yet, see CHANGELOG.md) while the SDK stays put. Lockstep is the
default; the scoped path is for a fix that cannot wait for the next stack release.

## Release in one command

You committed a few changes, each with a line under `[Unreleased]` in `CHANGELOG.md`. Now:

```
python3 tools/release.py 0.8.1 --push
```

- turns `[Unreleased]` into `## [0.8.1] — <today>` and opens a fresh empty `[Unreleased]`
- sets the version in the nine markers and the `zpodsdk~=` requirement in `zpodcli/pyproject.toml`
- runs `tools/release_pretest.sh`: `uv lock` in zpodsdk and zpodcli, the four suites, `uv build`
  of both wheels, and a check that the zpodcli wheel requires `zpodsdk~=0.8.1`; a failure
  restores the files and releases nothing
- commits `Release 0.8.1`, tags `v0.8.1`, pushes `main` and the tag

GitHub then runs `.github/workflows/release.yml` on the tag: the same checks, the `[0.8.1]`
section is published as the release note and marked latest, then `zpodsdk` is built and
published to PyPI, then `zpodcli` is built, installed into an empty environment against the SDK
just published, published, and both are attached to the release. About three minutes.
`just zpod-release 0.8.1` is the same command.

Add `--dry-run` to see the section and the plan without changing anything. `--from-commits`
fills `[Unreleased]` from the commit subjects first; `--draft` prints those candidates.

## Writing the entries

`CHANGELOG.md` is one file for four packages. Entries go under `[Unreleased]` as the change is
made, with a scope in bold where a line is package-specific (**API:**, **engine:**, **zcli:**,
**SDK:**). A release section opens with **Breaking** when there is one, then a heading per
component (zPod API, zPod Engine, zcli, zpodsdk, Stack and operations), each with Added /
Changed / Fixed / Removed inside as needed. The release note is that section verbatim, so what
reads well in the file reads well on GitHub.

## PyPI

The workflow publishes with `uv publish`, once per package, zpodsdk first. It uses, in this order:

1. the repository secret `PYPI_API_TOKEN`, when it is set (a PyPI API token scoped to both
   projects, or one token per project would need two secrets);
2. otherwise [trusted publishing](https://docs.pypi.org/trusted-publishers/): on pypi.org, for
   **each** of the projects `zpodsdk` and `zpodcli`, *Publishing*, add a GitHub publisher with
   owner `zPodFactory`, repository `zpodcore`, workflow `release.yml`, environment `pypi`. The
   same entry twice: a publisher is an allow-list on the project, and which project a wheel
   lands under comes from the wheel's own name. No secret to rotate.

The repository needs a `pypi` environment (Settings → Environments); a required reviewer on it
turns a publish into a click-to-approve step. Without a publisher or a token, the `pypi-*` jobs
fail and the GitHub release still exists with its notes; set one up and re-run the jobs.

## What stops a release

`release.py` refuses, before changing anything:

- a working tree that is not clean, or a branch other than `main`
- an empty `[Unreleased]` (nothing to say is not a release; `--from-commits` fills it)
- a version that is not above the newest tag, or that is not `X.Y.Z`
- a tracked `.env`, `*.log`, `docs/`, `runs/`, root `uv.lock` or `misc/` scratch file
- any string from `.release-denylist` in the tree or in the commits since the last tag. That file
  is local and git-ignored: names that must never enter the history.
- a failing pretest: markers that disagree, a version not above a scoped tag, a failing suite, a
  wheel that does not build or does not require the SDK released beside it

`python3 tools/release.py --check` runs the rules that must hold between releases too: the shipped
version equals the newest changelog section, every tag has a section, nothing local is tracked.
`.github/workflows/checks.yml` runs it on every push, with `version_markers.py --check` and the
four suites.

## Fixing a release note after the fact

Edit the section in `CHANGELOG.md`, commit, push. Then on GitHub: Actions, release, Run workflow,
version `0.8.0`. The release is updated in place; the tag never moves and nothing is re-published
to PyPI. A blank version republishes every tag, which is also how releases are backfilled for old
tags.

Never tag by hand, never edit a release in GitHub's editor: the file is the source, the release is a
copy.

## The configuration block

At the top of `release.py`:

| Setting | Meaning |
|---|---|
| `PROJECT` | name used in the tag message |
| `VERSION_FILE`, `VERSION_PATTERN` | where the shipped version is, and the regex (one group) that finds it; here the API's `__version__` |
| `VERSION_SHAPE` | `\d+\.\d+\.\d+` for the CLIs and packages, `\d+\.\d+(\.\d+)?` for packer |
| `VERSION_IN_FILE` | what is written into `VERSION_FILE`: `{version}`, or `{major_minor}` for packer |
| `REQUIRED_FILES` | files that must exist before a cut, e.g. `zbox-{major_minor}.json` |
| `ALSO_UPDATE` | other files carrying the version: here the other eight markers and the `zpodsdk~=` requirement |
| `TEST_COMMAND` | run before the commit; here `tools/release_pretest.sh` |
| `MUST_STAY_LOCAL` | regex for files that must never be tracked |

At the top of `release_notes.py`: `facts(version)`, markdown placed above the section. Here the
stack update command, the two PyPI install commands and the compatibility line.
