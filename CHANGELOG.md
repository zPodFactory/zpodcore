# Changelog

Notable changes to zpodcore, newest first. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). zpodcore is a monorepo with one
version for four packages: the zPod API, the zPod Engine (Prefect flows), `zcli` and `zpodsdk`.
A tag `vX.Y.Z` moves all of them, and publishes `zpodsdk` and `zpodcli` to PyPI. The API decides
the digit: minor when the API changes shape, patch otherwise; `zpodsdk` always carries the API's
version; `zcli X.Y.*` is built for API `X.Y.*`.

Entries say what changed for the person operating the stack or calling it, and why in a clause.
A release section opens with **Breaking** when there is one, then has one heading per component
(zPod API, zPod Engine, zcli, zpodsdk, Stack and operations) with Added / Changed / Fixed /
Removed inside as needed, so a reader with one hat reads one heading. The commit history has the
reasoning. The `0.x` line stays pre-1.0 while the shape can still move; a change that breaks an
endpoint, a flag or an output someone may parse is named in **Breaking**, which is what warns a
reader, not the digit.

**Cutting a release.** Changes land under `[Unreleased]` as they are made. When enough has
accumulated, `python3 tools/release.py X.Y.Z --push` does the rest: `[Unreleased]` becomes
`[X.Y.Z] — date`, the nine version markers and the `zpodsdk~=` requirement in `zpodcli` move
with it, `tools/release_pretest.sh` must pass (lockfiles, the four suites, both wheels), the
commit is tagged `vX.Y.Z` and pushed, and the tag publishes this file's section as the GitHub
release note and both packages to PyPI (`.github/workflows/release.yml`,
`tools/release_notes.py`). The script refuses a dirty tree, an empty `[Unreleased]`, a version
not above the last tag, a tracked `.env`, log, `docs/` or `runs/` file, and any string from the
local `.release-denylist`; `--check` runs the same rules, and CI runs it on every push. Preview a
note with `python3 tools/release_notes.py X.Y.Z`.

## [Unreleased]

### zPod Engine

#### Changed

- **Prefect 3.8.3 → 3.8.8** (server image, worker image base, flow environment,
  `prefect.yaml`), for the fixes between the two: a runner no longer reschedules a flow run the
  server already finished on SIGTERM, cancellation cleanup and pause-expiration monitors page
  through all runs, the worker healthcheck stays healthy while the API is in maintenance, the
  event persister survives a database `CancelledError`, runner names with dots are no longer
  truncated, and a scheduled-run polling fix from 3.8.5. python-slugify moves to 9.0.0 with it,
  and prefect-docker 0.7.3 → 0.7.4 in the flow environment and the worker image. The three carry
  a dated `exclude-newer-package` waiver in `zpodengine/pyproject.toml` until they are older than
  the 30-day quarantine (2026-11-05).

### Stack and operations

- **Release workflow: the zpodcli smoke install runs from outside the project**, because
  zpodcli's `exclude-newer = "30 days"` applies to `uv pip install` too and hid the zpodsdk
  uploaded a minute earlier, which left zpodcli 0.8.0 unpublished on the first run. A manual
  run of the workflow with a version and *publish* ticked now builds both packages from that
  version's tag and publishes them with `--check-url`, skipping files already on PyPI, so a
  publish that failed after the tag is completed without moving the tag.

## [0.8.0] — 2026-10-08

### Breaking

- **The mandatory core component is `zcore`, no longer `zbox`.** A profile must start with a
  `zcore-*` component; `POST /profiles` rejects `zbox-*` with 400. Management IP `.2`, DNS, NFS
  and the zboxapi endpoint (`zcore.<domain>`) belong to zcore; `zbox` is now an ordinary
  component. Run `just zcore-transition` once after upgrading to rewrite existing profiles (#60).
- **`GET /zpods/{id}/features` is gone; features are a JSON object on the zPod.** `features` is
  accepted on create and update and returned as a dict (was a list of rows). The migration drops
  the `zpod_features` table without carrying its rows over (#43).
- **zPod names and FQDNs are validated up front.** A name must be ASCII and start with a letter
  (406, #48). The longest component FQDN a profile would produce must fit in 64 minus
  `zpodfactory_fqdn_reserved_chars` characters (400, #65). The target endpoint must be `ACTIVE`
  (406, bed83e1).
- **Settings are readable by every authenticated user, and only the Broadcom token is masked.**
  At 0.7.2 any setting containing `password` or `ssh_key` came back as `********` and the list
  was superadmin-only. Now `zpodfactory_ssh_key`, `license_*` and a configured
  `ff_unique_zpod_password` are returned in clear to any user (449f149, bed83e1, #57).
- **409 responses carry resource-specific messages** (`zPod already exists`, `User already in
  group`, `Email already in use`…) instead of `Conflicting record found`; clients matching on
  the text must adapt (#35, #63).
- **The `customerconnect` and `avipulse` download engines are removed.** `https` is the only
  engine; library entries still declaring a removed engine end in `FAILED_UNSUPPORTED_ENGINE`.
  The `zpodfactory_customerconnect_*` settings are no longer seeded (#57).
- **Default management IPs changed by component name:** `hcx` (.45) removed; `hcx-cloud` .7 and
  `hcx-connector` .8 (63eaee8), `zrdp` .3 (30d032e), `vcfinstaller` .25 (c04e98e), `zcore` .2
  (#60).
- **zpodcli and zpodsdk on PyPI require Python 3.14.** The published pins were `>=3.10` and
  `>=3.8.1`. `uv tool install zpodcli` fetches the interpreter on its own; plain `pip` users
  need 3.14 installed (#49, #54, #71).
- **Prefect 2 → 3.** The server image is `prefecthq/prefect:3.8.3-python3.14`; the Prefect
  volume must be wiped on first start and the 7 deployments re-registered with
  `just zpodengine-deploy-all` (#50, #71).
- **zcli:** the auto-refresh flag on `zpod list` and `zpod component list` is `--watch/-w`, no
  longer `--wait` (#67).
- **`GET /` returns an HTML landing page** with an `X-zPod-API: true` header instead of the
  plain string (#41).

### zPod API

#### Added

- `GET /zpods/{id}/permissions/mine` returns the caller's effective permission, so a client can
  show or hide actions without listing every grant (#53).
- `DELETE /users/{id}/delete` removes a user and reassigns their zPods to the superuser; user 1
  cannot be deleted (7ebdeb1).
- `PATCH /users/{id}` accepts `email`, lower-cased and validated; a duplicate returns 409 (#63).
  `GET /users` includes `api_token` for superadmins and for your own row (#62).
- zPod components expose `password` and per-product `usernames` (`ui`, `ssh`, `ui-proxmox*`,
  `vcfinstaller`) (#41, 39c2aa6, 3071eb5); `vnics` and `vdisks` are accepted on zPod components
  and profile items (6ea6d95, 64fded5).
- `features` on zPod create and update, which is where config-scripts are selected per zPod
  (#43).
- **Optional VDS name on an endpoint**, `endpoints.compute.vds`, on create, update and view.
  When set, govc network mappings use the full inventory path `/dc/network/<vds>/<segment>`,
  which disambiguates same-named segments across switches that share an NSX transport zone;
  when empty, the bare segment name is used as before, so existing endpoints are unaffected.
  zcli prompts for it with an empty default (#61). The create schema defaults it to empty, so a
  client that omits the key keeps working.
- **Feature flags**, all plain `Setting` rows: `ff_unique_zpod_password` (#33),
  `ff_reuse_zpod_password` (#38), `ff_restrict_zpod_with_username_prefix` (#37),
  `ff_max_zpods_per_user` and per-user `ff_max_zpods_<username>` with superadmins exempt
  (fa5a1e3), `ff_default_config_scripts` (#43).
- **Settings seeded on every start.** `zpodfactory_load_default_settings.py` inserts missing
  defaults without overwriting existing values, so an upgraded instance gets new flags
  automatically. New: `zpodfactory_broadcom_download_token`, `zpodfactory_fqdn_reserved_chars`
  (8), `zpodfactory_debug_level` (INFO) (#55, #57, #65, f716b06).
- **Live log level**: `zpodfactory_debug_level` switches INFO/DEBUG without restart; at DEBUG
  the API logs request and response panels for all 15 routers (#55).

#### Changed

- Permissions: removing a component needs `ZpodMaintainer` (was any user); ENET create/delete
  is superadmin-only; DNS reads open to `ZpodReader`; removing the last OWNER/ADMIN user or
  group of a zPod is refused with 409 (#53).
- zPod name uniqueness is checked globally and ignores `DELETED` zPods, so a name can be reused
  after deletion and a user can no longer collide with a zPod they cannot see (cf00978).
  Generated passwords are 16 characters (VCF 5.2 minimum, #33); `ff_reuse_zpod_password` keeps
  the password of a same-name deleted zPod (#38).
- Library creation clones the repository before creating the row and cleans up on either
  failure (6c6b249). Disabling a component deletes its downloaded product file and resets the
  download status, so re-enabling re-downloads (#56).
- Dependabot: 131 of 136 alerts closed; `python-multipart` 0.0.9 → 0.0.32; unused `python-jose`
  and `passlib` dropped (#42, #69, #71).

#### Fixed

- `DELETE /zpods/{id}/permissions/{permission}/groups` returned 500 because of a keyword typo
  (#52).
- Non-superadmin `GET /zpods` returned duplicate rows and failed on the JSON column with
  DISTINCT (#45).
- FastAPI 0.141 changed operation-id generation, which would have renamed every SDK module; ids
  are now generated explicitly (#71).

#### Removed

- `zpod_features` table and `GET /zpods/{id}/features` (#43). `zpodfactory_customerconnect_*`
  settings are no longer seeded (#57).

### zPod Engine

#### Added

- **Config-scripts**: `zpod_deploy`, `zpod_destroy` and `zpod_component_add` run site-local
  scripts selected per zPod via `features["config-scripts"]`, with `CONFIG_SCRIPTS` and
  `POST_SCRIPTS` statuses. Samples ship under `config_scripts/sample/`; the rest of that
  directory stays local (#43, #45, #47).
- **OVA staging** (`ff_endpoint_ova_staging`): each L1 OVA is uploaded once to
  `components-staging` as a template and cloned per zPod with OVF properties injected; one
  stager is elected atomically, others wait up to 60 min; any failure falls back to direct
  `govc import.ova` (#59).
- **NSX orphan segment-port cleanup on destroy**: when a segment does not drain, ports are
  classified VIF → VM → transport node → vCenter and, with `ff_nsx_clean_orphan_ports`, ports
  whose VM no longer exists are deleted; ports whose VM still exists are never touched. Handles
  ports whose VIF record NSX already dropped (#66, #70).
- **Per-component VM customisation**: `vcpu`, `vmem`, `vnics` and `vdisks` (list of GB)
  applied after deploy; extra NICs only ever added. Extended from esxi/proxmox to every
  component, with the warning that it can break appliances (64fded5, 334fc80, ae1c9c8,
  bcb93c2).
- **New components**: Proxmox VE, Proxmox Datacenter Manager, Proxmox Backup Server (39c2aa6,
  eb3ea0d, 6c3cc3e); `vcfinstaller` for VCF 9 (c04e98e, 3071eb5); `hcx-cloud` and
  `hcx-connector` (63eaee8); `zrdp` default IP (30d032e).
- **Broadcom depot downloads**: `zpodfactory_broadcom_download_token` is substituted for
  `${BROADCOM_DOWNLOAD_TOKEN}` in library URLs, redacted in logs; 401/403 map to
  `FAILED_AUTHENTICATION` (#57).
- **Engine feature flags**: `ff_esxi_hostname_is_fqdn` (default true, William Lam ESXi
  templates, #33), `ff_component_wait_for_status` (NSX overall cluster status, #44),
  `ff_zpod_<name>_subnet` (pin a zPod's /24, 51e6a54), `ff_endpoint_ova_staging` (#59),
  `ff_nsx_clean_orphan_ports` (#66).
- terraform in the flow image (c622175, pinned 1.16.0 in #71).

#### Changed

- Only `zcore` gets core treatment in dispatch, DNS self-configuration and pre-scripts; `zbox`
  deploys like any other component (#60).
- NSX licences are applied in post-scripts from the component's licence entries, several NSX-T
  licence types in a loop; the wait is on the management cluster reaching `STABLE` (#36, #44,
  #48). Only IPv4 segments are fetched (cc1b79a).
- NSX calls retry 502/503/504 and transient errors with backoff, including auth, and surface
  the response body instead of a JSON decode error; vCenter lookups retry
  `ManagedObjectNotFound` and `VAppTaskInProgress` during parallel destroys (#58).
- Endpoint `resource_pool` accepts resource pools, not only clusters; `scaleDescendantsShares`
  is inherited from the parent instead of forced (#35, d5e2098).
- Prefect flows call `.result()` on their last future so a failed task fails the flow and fires
  `on_failure`; `cmd_execute` raises on a non-zero exit, so failed `vcsa-deploy`, `ovftool` and
  `7z` runs no longer complete green (#50).
- Download progress gives up after 30 s without growth; a checksum mismatch deletes the file
  before failing (#57).
- Flow image: PowerCLI 13.2.1 → VCF.PowerCLI 9.1.1, govc 0.34.2 → 0.56.0 (datastore clusters,
  605f65c), PowerShell 7.4.1 → 7.5.11, amd64-only, built with BuildKit; cold `deploy-all` about
  2m50s instead of 5–6 min and no leftover intermediate containers (#71).
- `PREFECT_API_URL` is the relative `/api`, so the Prefect UI works behind any hostname (#51).

#### Fixed

- Two zPods created in quick succession could be assigned the same network (b42cf68).
- `get_portgroups` type error broke endpoint verification (#58). The ESXi certificate checker
  no longer aborts the post-script on transient errors (8a36539). Component removal reads nested
  values in two steps (ab22e0c). httpx 0.28 behaviour change in the NSX client (20b20ac).

#### Removed

- Download engines `customerconnect` and `avipulse` and the `vcc` binary (#57).

### zcli

#### Added

- `zpod info <name> [-f bncd]` with Basic, Networking, Components (usernames and password) and
  DNS panels (0d89ec7, #64).
- `setting create` and `setting delete` (#33); `user delete` (7ebdeb1);
  `endpoint create --generate-config-sample` (29ed44f).
- `zpod list --owner` (8475254) and `--watch`; `zpod component list --watch`, sorted by IP
  (0d89ec7, #67).
- `zpod create --wait` with spinner, stopping on `DESTROY_FAILED` too; the endpoint is
  auto-selected when only one is visible and the profile from `ff_zpod_default_profile` when
  `-p` is omitted (9071f94, 0d89ec7, #67).
- `zpod component add --vnics` and `--vdisks` (64fded5, 9fff7ce).
- `--json/-j` and `--no-color` on every list, get and info command (62f4bb0, #67). `user list`
  shows the API Token column (#62); `user update --email`, `--superadmin/--no-superadmin` (#63,
  #67); endpoint `vds` prompt and column (#61).

#### Changed

- JSON output is plain when piped or with `--no-color`, so `zcli … -j | jq` works (#67).
  `component list -j` applies the same active/downloading filter as the table (#67).
  `factory list` shows full tokens (3a584fc). Setting `description` is prompted as mandatory
  (ac3ecd4). SVG captures use the Catppuccin Mocha theme (#71).
- The published wheel requires `zpodsdk~=<version>` (compatible release) instead of an exact
  pin, so a zpodcli-only patch can ship without an SDK upload.

#### Fixed

- `user update` wiped description and ssh_key and revoked superadmin when those flags were
  omitted; a no-op update is now rejected (#67).
- `endpoint create -ef` path handling (29ed44f); profile command regression (e46a60c); rich
  rendering glitch on required prompts (c31da6f).

### zpodsdk

- Regenerated from API 0.8.0 with openapi-python-client 0.29.0; package import stays `zpodsdk`,
  client class `ZpodClient` (#71).
- New modules `zpods_permissions_get_mine` and `users_delete`; new fields `vds`, `api_token`,
  `email` on update, `features`, `vnics`, `vdisks`, component `password` and `usernames`;
  statuses `CONFIG_SCRIPTS`, `POST_SCRIPTS`, `FAILED_UNSUPPORTED_ENGINE`.
- Removed: `zpods_features_*` and `ZpodFeatureView`.
- Dependencies: httpx 0.28.1, attrs 26.1.0; Python 3.14. The README on PyPI now shows the real
  import (`zpodsdk`, `ZpodClient`, the `access_token` header).

### Stack and operations

- **Releases follow the shared zPodFactory standard.** `tools/release.py` (cut, `--check`,
  `--draft`, `--from-commits`) and `tools/release_notes.py` are the same files as in every other
  repository, with a configuration block for the nine version markers; `tools/release_pretest.sh`
  refreshes the lockfiles, runs the four suites and checks the wheels before the commit;
  `.github/workflows/checks.yml` runs the rules and the suites on every push; `release.yml`
  publishes the note and both PyPI packages from the tag. `just zpod-release X.Y.Z` is the one
  command; bump-my-version is gone. `just zpod-update` refuses a dirty tree with a non-zero exit
  and waits for the API instead of sleeping.
- **Appliance bootstrap**: `appliance/bootstrap/zpodfactory-stack.sh`, fetched by the
  zPodFactory OVA at first boot, installs the host toolchain, clones and starts the stack,
  registers the factory, seeds settings, creates the default library, enables `zcore-13.5`, then
  brings up zpodweb and prepares the VCF offline depot (#68).
- **Poetry → uv** everywhere, per-subproject `uv.lock`, hatchling for the two wheels,
  `exclude-newer = "30 days"`; local `uv sync` of zpodapi or zpodengine needs `gcc` and
  `libpq-dev` (#49, #71).
- **Postgres** 15.2-bullseye → 15.19-trixie; a wrapper entrypoint reindexes and refreshes
  collation on existing volumes before accepting connections (#71).
- **Test baseline** in all four subprojects and `just zpod-runtests` (#54, #62, #63, #65, #66).
- Platform, 0.7.2 → 0.8.0: Python 3.12.1 → 3.14.7 (slim-trixie images); FastAPI 0.111.0 →
  0.141.1; SQLModel 0.0.18 → 0.0.39; Alembic 1.13.1 → 1.19.1; uvicorn 0.29.0 → 0.52.4 and
  gunicorn 22.0.0 → 26.2.0 with `uvicorn-worker`; pyvmomi 8.0.2.0.1 → 9.1.0.0; Prefect
  2.19.2 → 3.8.3 with prefect-docker 0.7.3; openapi-python-client 0.20.0 → 0.29.0 (no `click`
  pin); typer 0.12.3 → 0.27.1 and pydantic 2.7.1 → 2.13.4 in zcli.

## [0.7.2] — 2024-06-27

### Changed

- Python package versions pinned; the unused `vsphere-automation-sdk-python` dependency removed
  (b3f031b).

## [0.7.1] — 2024-06-26

### Fixed

- Component upload called its upload method incorrectly (e149069).

## [0.7.0] — 2024-06-25

### Added

- Component upload: `POST /components/upload` and `zcli component upload` (#32), with a simple
  `component_json` loader (4c951a1).
- zPod DNS management: API routes, `zcli zpod dns`, and records updated on component add and
  remove (9f83e9d, 2b8a4fe).

### Changed

- The `vcf` component is renamed `cloudbuilder` (7fa0b08); IPs are unique per zPod (53b5add);
  NSX auth goes through `auth_by_zpod` (1a945de); default SVG theme `DIMMED_MONOKAI` (8b4ffa5);
  update commands moved into the justfile (05a51a1); packages updated, incl. jinja2 3.1.4, idna
  3.7, requests 2.32.2 (#27, #28, #29, #30, #31).

### Fixed

- Renaming a component only requires `component_uid` to be unique (81c9b17); settings default
  descriptions (3795ca1); examples (f71e56d).

## [0.6.1] — 2024-05-07

### Added

- SVG output for zcli (`--output-svg`) (2ca25ca).

### Changed

- Prefect 2.18.1 (ad30ac8); enet commands only for `nsxt_projects` endpoints (4bdbcad);
  `docker-compose.dev.yaml` became the default compose file (cc1b873); idna 3.7 in
  zpodsdk_builder (#26).

### Fixed

- Endpoint server error on enet list (ebc9a54); `httpx.RequestError` captured (2ad3099);
  endpoint get `where` criteria (3e08f15).

## [0.6.0] — 2024-04-30

### Added

- Endpoint management capabilities in the API and zcli (8e91fe9); additional zPod component
  input validations (548890c); prechecks before a release build (cba9826); labels (c63419b).

### Changed

- `DEV_MODE` setting refactored (1ddd123); endpoint passwords hidden in interactive mode
  (f5eeaea); JSON formatter for profile output (08dccf5); `None` values hidden (b348a09);
  gunicorn 22.0.0 (#25).

## [0.5.0] — 2024-03-26

### Fixed

- zpodsdk versioning (fab85fe). Otherwise identical to 0.4.0.

## [0.4.0] — 2024-03-26

First tagged release of the full stack after the initial development run: the `zcli` command
set (#14, #16, #24), endpoints (#13), libraries and component download with checksum
verification (#8, #10), Prefect 2.8.5 with concurrency limits (#11).

## [0.3.0] — 2024-03-07

Initial release.
