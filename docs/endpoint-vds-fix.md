# Endpoint: add/update VDS name

## Problem

A zpodfactory `Endpoint`'s compute config (`endpoints.compute`) currently
tracks vCenter connection details, credentials, datacenter, resource pool,
datastore, and VM folder — but has no field for the vSphere Distributed
Switch (VDS) name. There is also no way to update most compute fields after
creation: `EndpointComputeUpdate` only exposes `username`/`password` today.

Goal: add a `vds` field alongside the existing compute fields, settable at
creation and updatable afterwards, end-to-end (API → SDK → CLI).

## Current shape (for reference)

`endpoints.compute` fields today, defined in
`zpodapi/src/zpodapi/endpoints/endpoint__schemas.py`:

```
driver, hostname, username, password, datacenter, resource_pool,
storage_policy, storage_datastore, contentlibrary, vmfolder
```

`Endpoint.endpoints` (`zpodcommon/src/zpodcommon/models/endpoint_models.py`)
is a raw `JSON` column — no DB migration is needed to add a new key, but it
does mean **existing rows won't have a `vds` key** until explicitly updated.
`EndpointService.update()` merges partial updates into that JSON generically
via `update_dictionary()`, so any field added to `EndpointComputeUpdate`
"just works" for PATCH without further service-layer changes.

The SDK (`zpodsdk`) is generated from the API's OpenAPI spec via
`zpodapi/scripts/openapi/generate_openapi_json.py` +
`openapi-python-client` (see `zpodsdk_builder/`), so any schema change must
be followed by a client regeneration before the CLI can use it.

## Compatibility risk

`EndpointComputeView` fields are currently all required (`Field(..., ...)`).
If `vds` is added as required, `GET /endpoints` will raise a validation
error (500) for any pre-existing endpoint whose JSON blob doesn't yet
contain a `vds` key — the same trap `storage_policy`/`contentlibrary` would
have hit when they were introduced. To avoid breaking existing endpoints on
read, `vds` should default to `""` in the **view** schema (so the field is
optional on the way out) while still being requested (default `""`,
consistent with how `storage_policy`/`contentlibrary` are handled today) on
create, then backfilled per-endpoint via the new update path.

## Plan (implemented)

### 1. API schema — `zpodapi/src/zpodapi/endpoints/endpoint__schemas.py` ✅
- Added `vds = {"example": "my-vds"}` to `D.compute`.
- Added `vds: str = Field(..., D.compute.vds)` to `EndpointComputeCreate`
  (required key, empty string allowed as a value — same pattern as
  `storage_policy`/`contentlibrary`).
- Added `vds: str = Field("", D.compute.vds)` to `EndpointComputeView`
  (default `""` so existing rows without the key still deserialize).
- Added `vds: str | None = Field(None, D.compute.vds)` to
  `EndpointComputeUpdate` (which previously only had `username`/`password`).

No changes were needed in `endpoint__services.py` or `endpoint__utils.py` —
`update_dictionary()` already merges arbitrary keys generically, so the new
field is updatable via `PATCH /endpoints/{id}` (`endpoints.compute.vds`) as
soon as it exists on the schema.

### 2. Regenerate the SDK client ✅
Ran `just zpodsdk-update` (execs into the running `zpodapi` dev container to
dump `openapi.json`, then builds/runs the `zpodsdk_builder` image to update
`zpodsdk/src/zpodsdk`). `endpoint_compute_create.py`, `endpoint_compute_view.py`,
and `endpoint_compute_update.py` all now carry `vds`.

### 3. CLI — `zpodcli/src/zpodcli/cmd/endpoint_cli.py` ✅
- `generate_table()`: added `"vds"` to `compute_endpoint_keys` so it shows in
  `endpoint list` / `endpoint info`.
- `endpoint_create()` interactive flow: added `"vds": ask("vds", default="")`
  to the compute dict (mirrors `vmfolder`, but optional/blank-friendly).
- `endpoint_generate_sample()`: added `"vds": ""` to the sample compute JSON.
- **No dedicated `--compute-vds` flag was added to `endpoint update`.**
  `vds` travels like any other compute field — via the normal create payload
  (interactive prompt, `--endpoints`/`--endpoints-file` JSON, or the sample
  file) — not as a special-cased update flag. Updating `vds` on an existing
  endpoint today means going through the API/SDK directly (`PATCH
  /endpoints/{id}` with `endpoints.compute.vds`) rather than a CLI flag; a
  CLI update flag can be added later if this becomes a frequent operation.

### 4. Downstream usage ✅ (implemented — see §6 below)
Originally scoped as "out of scope," but a follow-up request wired `vds`
into `ovfdeployer.py`'s govc network mapping (§6). No other deploy code
consumes `compute["vds"]`; NSX-T segment placement is still driven by
`network.transportzone`, not the VDS name.

### 5. Backfilling existing endpoints
Since `endpoints` is a JSON blob, no Alembic migration applies. Existing
endpoints read back with `vds=""` and stay that way — it is **only enforced
when set**: `ovfdeployer.py` (§6) falls back to the pre-change bare-name
behavior whenever `vds` is empty, so there's no functional requirement to
backfill every endpoint. Setting `vds` on an existing endpoint requires a
direct `PATCH /endpoints/{id}` call (see §3) until/unless a CLI flag is
added.

## 6. ovfdeployer: qualify the govc network mapping with the VDS path

### Problem
`zpodengine/src/zpodengine/lib/ovfdeployer.py` builds the per-zPod portgroup
name as a bare string (`f"{site_id}-{zpod.name}-segment"`) and renders it
into the component's `component_deploy_govc_spec` (Jinja `zpod_portgroup`
variable), which becomes part of the OVF options JSON handed to
`govc import.ova -options=...`.

In environments where multiple clusters share the same NSX-T overlay
transport zone but sit on different VDS's, the zpod segment portgroup gets
created on every one of those VDS's under the same name (each with its own
identifier). `govc import.ova` then can't tell which of the
identically-named portgroups to attach to and fails.

### Fix (implemented)
`govc`'s own object finder (unlike the pyVmomi calls elsewhere in this repo)
resolves full inventory paths, so the govc-facing value is now built as:

```
/{datacenter}/network/{vds_name}/{site_id}-{zpod_name}-segment
```

This only applies to the value fed into the **govc JSON template**
(`zpod_portgroup` Jinja variable → `NetworkMapping`/network fields in the
options file consumed by `govc import.ova`). It does **not** apply to
`vCenter.get_portgroup()` (`zpodcommon/src/zpodcommon/lib/vmware.py`), which
is used by the OVA-staging clone path (`ff_endpoint_ova_staging` →
`ova_staging.deploy_from_template` → `vCenter.clone_template` →
`nic_portgroup_changes`). That pyVmomi lookup matches on the bare `.name`
property of `vim.Network` objects, not a path string — passing it a full
path would simply never match. So `ovfdeployer.py` now carries **two**
variables:

- `zpod_portgroup` — bare segment name (`{site_id}-{zpod.name}-segment`),
  unchanged, still passed as `portgroup_name=` to `deploy_from_template()`.
- `zpod_portgroup_path` — VDS-qualified inventory path, used only for the
  Jinja render that feeds the `govc import.ova` options JSON.

If no VDS is configured (`compute.vds` is still `""` — not yet backfilled,
see compatibility note above), there's only one portgroup with that name on
the endpoint and govc resolves it fine by bare name, so
`zpod_portgroup_path` falls back to `zpod_portgroup` — preserving today's
behavior until an admin sets `vds`. L2 (nested) deployments have no VDS
concept and keep using the hardcoded `"VM Network"` bare name for both
variables.

### Known follow-up (not implemented here)
The OVA-staging clone path (`vCenter.clone_template`/`get_portgroup`) is
still a bare-name pyVmomi lookup, so it remains ambiguous if multiple
portgroups share a name across VDS's on the same vCenter. Disambiguating
that path would require either scoping `get_obj`'s container view to the
target VDS, or matching on the DVPortgroup's `config.distributedVirtualSwitch`
reference. Flagging as a gap, not fixing now since it wasn't part of this
request.

### Worked examples

**Endpoint "homelab-01"** — `datacenter=Datacenter-1`, `vds=vds-01`,
`SITE_ID` default (`zpod`), zPod name `lab42`:

```
/Datacenter-1/network/vds-01/zpod-lab42-segment
```

**Endpoint "homelab-02"** — `datacenter=DC-West`, `vds=DSwitch-Prod`,
`SITE_ID=site2`, zPod name `demo-nsx`:

```
/DC-West/network/DSwitch-Prod/site2-demo-nsx-segment
```

**Endpoint "homelab-03"** — `datacenter=Datacenter`, `vds=vds-homelab`,
`SITE_ID=lab`, zPod name `training7`:

```
/Datacenter/network/vds-homelab/lab-training7-segment
```

**Endpoint not yet backfilled** — `datacenter=Datacenter-1`, `vds=""`
(pre-existing endpoint, update not yet run), zPod name `legacy1`:

```
zpod-legacy1-segment
```
(falls back to the bare name — identical to pre-change behavior — until
`vds` is set via a direct `PATCH /endpoints/{id}` call)

## Testing plan
- `zpod endpoint create` (interactive) prompts for and stores `vds`.
- `zpod endpoint create --generate-config-sample` includes `"vds": ""`.
- `PATCH /endpoints/{id}` with `{"endpoints": {"compute": {"vds": "<name>"}}}`
  updates only `vds`, leaving other compute fields untouched (verify via
  `endpoint info -j`).
- `GET /endpoints` on an endpoint predating this change still returns
  200 with `compute.vds == ""` (no validation error).
- `zpod endpoint list` / `endpoint info` display the new `vds` column.
- Deploying an L1 component against an endpoint with `vds` set produces a
  `govc import.ova` options file whose network mapping is the full
  `/{datacenter}/network/{vds}/{segment}` path (check the printed "govc ovf
  property options generated file" log line).
- Deploying against an endpoint with `vds=""` still produces the bare
  segment name (no regression for endpoints not yet backfilled).
- With `ff_endpoint_ova_staging` enabled, the staged-clone path still
  receives the bare `portgroup_name` and clones successfully (unaffected by
  the `vds` change).
