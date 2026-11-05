# Profile fixtures

Drop profile JSON samples here as `<name>.json`. Each file's content is the
**raw `profile` array** from the zpodcore `ProfileCreate` schema - a list of
component items (or lists of items, for parallel-deployable groups), e.g.:

```json
[
    {"component_uid": "zcore-13.7", "hostname": "zcore"}
]
```

Not a full `{"name": ..., "profile": [...]}` wrapper - just the array. The
filename (minus `.json`) becomes the fixture's logical name; tests give the
actual `Profile` record created in zpodcore a run-scoped name like
`e2e-<filename>-<run_id>` so it never collides with a real profile of the
same name.

Every component referenced by a profile must already be `ACTIVE` in the
target zPodFactory's component library before a zpod can be deployed from
that profile - the suite does not enable components on your behalf as part
of profile tests.

`zcore.json` is special-cased by the `zcore_profile` fixture and used
pervasively across the suite (smoke test, permission-role deploy checks,
`ff_endpoint_ova_staging` toggle checks) - it should be the simplest
possible single-component profile.

If this directory has no `*.json` files (besides this README), every
profile-parametrized test collects zero cases and is skipped cleanly - the
suite is not blocked on these samples existing.
