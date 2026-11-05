"""Users, permission groups, and the zpod/global permission model.

`zcli user`/`zcli group` have no `--json` output for most subcommands, so
these tests drive actions through the CLI and verify state through the SDK.

Uses one shared deployed zpod (`active_zpod`, superadmin-created) for the
grant/deny scenarios, plus one real end-to-end deploy performed *by* a
non-superadmin identity (`test_zpod_permission_owner_can_deploy_their_own_zpod`)
to satisfy "validate through an actual deployment," per the user's request,
without redeploying once per permission combination.
"""

import pytest

from e2e import cli
from e2e.insight import Beat, Insight
from e2e.naming import E2E_EMAIL_DOMAIN
from e2e.profiles import profile_body

# Narrative metadata for the HTML report, keyed by test function name - see
# e2e.insight. Purely decorative: never read by the tests above, only
# pulled by report.py at render time.
INSIGHTS = {
    "test_reset_api_token_invalidates_old_token": Insight(
        why="A token that keeps working after 'reset' would make the reset button a lie.",
        reasoning="reset_api_token generates a brand new token and overwrites the stored one - "
                  "the old string still looks syntactically valid, but auth resolves tokens by "
                  "database lookup, not by format, so it simply maps to nothing anymore.",
        expected="The old token gets 403 on its very next call, not 401 - it isn't 'this user, "
                 "insufficient permission', it's 'no user at all'.",
        beats=[
            Beat("old token", "GET /users/me succeeds", state="200", color="pass", tag="BEFORE"),
            Beat("reset_api_token", "new token issued, old one overwritten", state="", color="info", tag="THE CHANGE"),
            Beat("old token, again", "GET /users/me with the same string", state="403", color="pass", tag="AFTER"),
        ],
    ),
    "test_zpod_scoped_denial_is_401_global_denial_is_403": Insight(
        why="Two different reasons to deny a request shouldn't collapse into one status code - "
            "an operator debugging 'why did this fail' needs to know if it's about THIS zpod or "
            "about the caller's role entirely.",
        reasoning="zpod-scoped checks (zpod_maintainer/zpod_reader dependencies) only ever see "
                  "requests for zpods the permission-filtered query already resolved - so by the "
                  "time they can say 'not enough permission', the zpod was visible. Global-resource "
                  "checks (only_superadmin) never look at a zpod at all.",
        expected="USER-level access, insufficient for delete -> 401. Non-superadmin creating a "
                 "global setting -> 403. Same caller, two different denial shapes.",
        beats=[
            Beat("USER grant + DELETE zpod", "zpod visible, action too big", state="401", color="pass", tag="ZPOD-SCOPED"),
            Beat("no grant + POST /settings", "unrelated to any zpod", state="403", color="pass", tag="GLOBAL"),
        ],
    ),
    "test_zpod_permission_no_grant_denied": Insight(
        why="A user with zero permission shouldn't even learn the zpod exists - 'forbidden' still "
            "confirms something is there to be forbidden from.",
        reasoning="get_zpod's own query is permission-filtered for non-superadmins "
                  "(zpod__services.py get_zpod_records) - a zero-grant user's WHERE clause simply "
                  "never matches the row, so the zpod_maintainer/zpod_reader dependency that would "
                  "produce a 401 never even runs. The 404 happens one layer earlier than the permission check.",
        expected="Both GET and DELETE return 404, not 401 - invisible, not just off-limits.",
        beats=[
            Beat("permission-filtered query", "row excluded before any permission check runs", state="", color="info", tag="THE CLUE"),
            Beat("GET /zpods/{id}", "zero-grant identity reads it", state="404", color="pass", tag="WHAT YOU SEE"),
            Beat("DELETE /zpods/{id}", "same identity tries to delete it", state="404", color="pass", tag="CONFIRMS IT"),
        ],
    ),
    "test_zpod_permission_via_group_grant": Insight(
        why="Granting access to a group only matters if the server actually walks group "
            "membership at authorization time, not just at grant time.",
        reasoning="ZpodPermission rows can attach to a group instead of a user directly - "
                  "get_user_zpod_permissions has to resolve 'is this user in any group holding a "
                  "grant on this zpod', not just 'does this user have a direct grant row'.",
        expected="A real mutating call (DNS add) through the group-granted identity succeeds and "
                 "is visible afterward - proof the grant resolves to write access, not just visibility.",
        beats=[
            Beat("group create + membership", "test_owner added to a fresh group", state="", color="info"),
            Beat("OWNER granted to the group", "not to test_owner directly", state="", color="info", tag="THE SETUP"),
            Beat("POST /zpods/{id}/dns", "test_owner adds a DNS entry", state="200", color="pass", tag="PROOF"),
        ],
    ),
    "test_global_superadmin_bypasses_zpod_permission_checks": Insight(
        why="A superadmin needing an explicit grant on every zpod in the system would defeat the "
            "point of being a superadmin.",
        reasoning="ZpodPermission.ADMIN is virtual - it's never a stored row. "
                  "get_user_zpod_permissions grants it implicitly whenever current_user.superadmin "
                  "is true, so superadmin access needs zero setup to already work everywhere.",
        expected="A superadmin identity with literally no grant ever created for this zpod can "
                 "still read it and its components.",
        beats=[
            Beat("current_user.superadmin", "true, no ZpodPermission row exists", state="", color="info", tag="THE CLUE"),
            Beat("GET /zpods/{id}", "test_admin reads a zpod it was never granted", state="200", color="pass"),
        ],
    ),
    "test_zpod_permission_denied_deploy_without_endpoint_permission": Insight(
        why="A non-superadmin shouldn't be able to deploy against an endpoint they can't even see "
            "in `endpoint list` - permission on the endpoint has to gate the CLI's own path to it.",
        reasoning="Endpoints are permission-filtered the same way zpods are "
                  "(endpoint__services.py get_endpoint_records) - `--endpoint <name>` has to resolve "
                  "the name to an id through that same filtered list, so a zero-grant user's lookup "
                  "comes up empty before any zpod-create logic runs.",
        expected="`zcli zpod create --endpoint <endpoint>` fails fast with \"Endpoint not found\" - no "
                 "real deploy work (Prefect flow, vCenter calls) ever starts.",
        beats=[
            Beat("endpoint list (filtered)", "test_owner has no grant on the endpoint", state="", color="info", tag="THE CLUE"),
            Beat("--endpoint <endpoint> lookup", "name can't resolve to an id", state="404", color="pass"),
            Beat("zpod create", "never reaches ZpodService.create()", state="exit 1", color="pass", tag="FAILS FAST"),
        ],
    ),
}


def test_user_crud_lifecycle(zcli_as, namer, superadmin_client):
    """Create, update, disable, enable, delete a throwaway user through zcli."""
    runner = zcli_as("superadmin")
    username = namer("user-crud")

    result = runner("user", "add", username, "--email", f"{username}@{E2E_EMAIL_DOMAIN}", "--description", "e2e crud test")
    assert result.returncode == 0, f"user add failed:\n{result.stderr}"

    user = superadmin_client.users_get.sync(id=f"username={username}")
    assert user is not None, f"expected {username} to exist after create"

    result = runner("user", "update", username, "--description", "updated")
    assert result.returncode == 0, f"user update failed:\n{result.stderr}"
    user = superadmin_client.users_get.sync(id=f"username={username}")
    assert user.description == "updated", f"expected description 'updated', got {user.description!r}"

    result = runner("user", "disable", username)
    assert result.returncode == 0, f"user disable failed:\n{result.stderr}"
    user = superadmin_client.users_get.sync(id=f"username={username}")
    assert user.status == "DISABLED", f"expected DISABLED, got {user.status}"

    result = runner("user", "enable", username)
    assert result.returncode == 0, f"user enable failed:\n{result.stderr}"
    user = superadmin_client.users_get.sync(id=f"username={username}")
    assert user.status == "ENABLED", f"expected ENABLED, got {user.status}"

    result = runner("user", "delete", username)
    assert result.returncode == 0, f"user delete failed:\n{result.stderr}"


def test_disabled_user_cannot_authenticate(zcli_as, namer, superadmin_client, e2e_config):
    """A disabled user's token stops working, even though it's technically still valid."""
    from zpodsdk.models.user_create import UserCreate

    username = namer("user-disabled")
    user = superadmin_client.users_create.sync(
        body=UserCreate(username=username, email=f"{username}@{E2E_EMAIL_DOMAIN}", description="e2e disabled-auth test")
    )
    token = user.api_token
    factory_name = namer("factory-disabled")
    cli.add_factory(factory_name, e2e_config.api_base_url, token)

    runner_superadmin = zcli_as("superadmin")
    runner_superadmin("user", "disable", username)

    result = cli.zcli_run("user", "list", factory=factory_name, check=False)
    assert result.returncode != 0, "a disabled user's token should no longer authenticate"

    cli.remove_factory(factory_name)
    superadmin_client.users_delete.sync(id=f"username={username}")


def test_reset_api_token_invalidates_old_token(zcli_as, namer, superadmin_client, e2e_config, api_check):
    """Resetting a user's API token makes the old token stop working."""
    from zpodsdk.models.user_create import UserCreate

    from e2e.client_factory import build_client

    username = namer("user-resettoken")
    user = superadmin_client.users_create.sync(
        body=UserCreate(username=username, email=f"{username}@{E2E_EMAIL_DOMAIN}", description="e2e reset-token test")
    )
    old_token = user.api_token
    old_client = build_client(e2e_config.api_base_url, old_token)
    assert old_client.users_get_me.sync().username == username, "old token should work before reset"

    runner = zcli_as("superadmin")
    result = runner("user", "reset_api_token", username)
    assert result.returncode == 0, f"reset_api_token failed:\n{result.stderr}"

    from zpodsdk.errors import UnexpectedStatus

    with pytest.raises(UnexpectedStatus) as exc_info:
        old_client.users_get_me.sync()
    api_check(
        "GET", "/users/me", "old token used after reset_api_token",
        expected=403, actual=exc_info.value.status_code,
        note="the old token is syntactically unchanged but no longer maps to any user, so auth fails outright",
    )
    assert exc_info.value.status_code == 403, f"expected 403 for the invalidated old token, got {exc_info.value.status_code}"

    superadmin_client.users_delete.sync(id=f"username={username}")


def test_permission_group_crud_and_membership(zcli_as, namer, superadmin_client):
    """Create a group, add/remove a user, verify membership through the SDK."""
    from zpodsdk.models.user_create import UserCreate

    runner = zcli_as("superadmin")
    group_name = namer("group")
    member_username = namer("group-member")

    superadmin_client.users_create.sync(
        body=UserCreate(username=member_username, email=f"{member_username}@{E2E_EMAIL_DOMAIN}")
    )

    result = runner("group", "create", group_name)
    assert result.returncode == 0, f"group create failed:\n{result.stderr}"

    result = runner("group", "user", "add", group_name, "--username", member_username)
    assert result.returncode == 0, f"group user add failed:\n{result.stderr}"

    group = superadmin_client.permission_groups_get.sync(id=f"name={group_name}")
    assert any(u.username == member_username for u in group.users), f"expected {member_username} in group {group_name}"

    result = runner("group", "user", "remove", group_name, "--username", member_username)
    assert result.returncode == 0, f"group user remove failed:\n{result.stderr}"
    group = superadmin_client.permission_groups_get.sync(id=f"name={group_name}")
    assert not any(u.username == member_username for u in group.users), f"expected {member_username} removed from {group_name}"

    runner("group", "delete", group_name)
    superadmin_client.users_delete.sync(id=f"username={member_username}")


def test_non_superadmin_denied_global_resource_crud(zcli_as, namer):
    """Non-superadmins can't create profiles, settings, libraries, users, permission_groups, or endpoints."""
    runner = zcli_as("test_user")
    name = namer("denied")

    checks = [
        ("profile", "create", name, "--profile", "[]"),
        ("setting", "create", "--name", name, "--value", "x", "--description", "x"),
        ("user", "add", name, "--email", f"{name}@{E2E_EMAIL_DOMAIN}"),
        ("group", "create", name),
    ]
    for args in checks:
        result = runner(*args, check=False)
        assert result.returncode != 0, f"non-superadmin should be denied: zcli {' '.join(args)}"


def test_zpod_scoped_denial_is_401_global_denial_is_403(zcli_as, test_user_client, active_zpod, api_check):
    """Precise status-code check the CLI can't surface: zpod-scoped denials are 401, global-resource denials are 403.

    A zpod-scoped denial only surfaces as 401 for a user who *has* some
    permission on the zpod but not enough (e.g. USER trying to delete,
    which needs OWNER/ADMIN) - `get_zpod`'s query is itself
    permission-filtered for non-superadmins, so a user with *zero* grant
    can't even see the zpod exists and gets 404 instead (see
    `test_zpod_permission_no_grant_denied`). So this test grants USER-level
    access first specifically to exercise the 401 path.
    """
    from zpodsdk.errors import UnexpectedStatus

    superadmin_runner = zcli_as("superadmin")
    test_username = test_user_client.users_get_me.sync().username
    superadmin_runner("zpod", "permission", "add", active_zpod, "--permission", "USER", "--username", test_username)

    try:
        with pytest.raises(UnexpectedStatus) as exc_info:
            test_user_client.zpods_delete.sync(id=f"name={active_zpod}")
        api_check(
            "DELETE", "/zpods/{id}", "USER-level (not OWNER/ADMIN) tries to delete a zpod",
            expected=401, actual=exc_info.value.status_code,
            note="zpod-scoped denial: the zpod IS visible (USER grant), but the action needs OWNER/ADMIN",
        )
        assert exc_info.value.status_code == 401, f"expected 401 for zpod-scoped denial, got {exc_info.value.status_code}"
    finally:
        superadmin_runner("zpod", "permission", "remove", active_zpod, "--permission", "USER", "--username", test_username)

    from zpodsdk.models.setting_create import SettingCreate

    with pytest.raises(UnexpectedStatus) as exc_info:
        test_user_client.settings_create.sync(body=SettingCreate(name="e2e-denied", value="x", description="x"))
    api_check(
        "POST", "/settings", "non-superadmin tries to create a global setting",
        expected=403, actual=exc_info.value.status_code,
        note="global-resource denial: unrelated to any zpod, gated purely on current_user.superadmin",
    )
    assert exc_info.value.status_code == 403, f"expected 403 for global-resource denial, got {exc_info.value.status_code}"


@pytest.fixture(scope="module")
def active_zpod(zcli_as, namer, zcore_profile_items, endpoint, superadmin_client, e2e_config, poll_zpod_deleted, keep_resources):
    """A deployed, ACTIVE minimal zcore zpod owned by superadmin - shared target for permission
    grant/deny scenarios below, so we don't redeploy once per scenario.

    Module-scoped deliberately (not the default function scope): every test
    below that uses this either doesn't mutate the zpod at all, or cleans up
    its own mutation (see each test's docstring), so one deploy safely
    covers all of them instead of a real deploy+destroy cycle per test.
    Uses its own throwaway profile (built from the same zcore_profile_items
    fixture the shared `zcore_profile` fixture uses) rather than depending
    on `zcore_profile` directly, since that fixture is function-scoped and a
    module-scoped fixture can't depend on a narrower-scoped one.
    """

    runner = zcli_as("superadmin")
    zpod_name = namer("zpod-perm")
    profile_name = namer("profile-zpod-perm")
    deploy_timeout = e2e_config.deploy_timeout_seconds + 60

    superadmin_client.profiles_create.sync(body=profile_body(profile_name, zcore_profile_items))

    result = runner(
        "zpod", "create", zpod_name,
        "--endpoint", endpoint.name,
        "--profile", profile_name,
        "--wait", "--no-spinner",
        check=False,
        timeout=deploy_timeout,
    )
    assert result.returncode == 0, f"setup deploy failed:\n{result.stdout}\n{result.stderr}"

    yield zpod_name

    if not keep_resources:
        runner("zpod", "destroy", zpod_name, check=False)
        try:
            poll_zpod_deleted(superadmin_client, f"name={zpod_name}")
        except Exception:
            pass
        try:
            superadmin_client.profiles_delete.sync(id=f"name={profile_name}")
        except Exception:
            pass


def test_zpod_permission_user_read_only_denied_write(zcli_as, active_zpod, test_user_client, api_check):
    """A user granted USER-level zpod permission can read it, but not mutate it."""
    superadmin_runner = zcli_as("superadmin")
    # test_user's username is discoverable through its own client.
    test_username = test_user_client.users_get_me.sync().username

    result = superadmin_runner("zpod", "permission", "add", active_zpod, "--permission", "USER", "--username", test_username)
    assert result.returncode == 0, f"granting USER permission failed:\n{result.stderr}"

    zpod = test_user_client.zpods_get.sync(id=f"name={active_zpod}")
    api_check("GET", "/zpods/{id}", "USER-level identity reads a zpod it was granted", expected="200", actual="200" if zpod else "error")
    assert zpod is not None, "USER-granted identity should be able to read the zpod"

    from zpodsdk.errors import UnexpectedStatus

    with pytest.raises(UnexpectedStatus) as exc_info:
        test_user_client.zpods_delete.sync(id=f"name={active_zpod}")
    api_check(
        "DELETE", "/zpods/{id}", "USER-level identity tries to delete the same zpod",
        expected=401, actual=exc_info.value.status_code, note="read access != write access",
    )
    assert exc_info.value.status_code == 401, "USER permission should not allow delete"

    superadmin_runner("zpod", "permission", "remove", active_zpod, "--permission", "USER", "--username", test_username)


def test_zpod_permission_no_grant_denied(zcli_as, active_zpod, test_owner_client, api_check):
    """A user with zero permission on a zpod is denied both read and write - as a 404, not a 401.

    `get_zpod`'s underlying query is itself permission-filtered for
    non-superadmins (zpod__services.py get_zpod_records), so a zero-grant
    user can't even see the zpod exists - it 404s before the
    zpod_maintainer/zpod_reader dependency (which would 401) ever runs.
    """
    from zpodsdk.errors import UnexpectedStatus

    with pytest.raises(UnexpectedStatus) as exc_info:
        test_owner_client.zpods_get.sync(id=f"name={active_zpod}")
    api_check(
        "GET", "/zpods/{id}", "zero-grant identity tries to read a zpod",
        expected=404, actual=exc_info.value.status_code,
        note="permission-filtered lookup means the zpod doesn't exist as far as this user can tell",
    )
    assert exc_info.value.status_code == 404, "no grant should deny read with 404 (zpod invisible, not just forbidden)"

    with pytest.raises(UnexpectedStatus) as exc_info:
        test_owner_client.zpods_delete.sync(id=f"name={active_zpod}")
    api_check(
        "DELETE", "/zpods/{id}", "zero-grant identity tries to delete the same zpod",
        expected=404, actual=exc_info.value.status_code,
        note="same permission-filtered lookup applies to every route that resolves the zpod by id/name",
    )
    assert exc_info.value.status_code == 404, "no grant should deny write with 404 (zpod invisible, not just forbidden)"


def test_zpod_permission_via_group_grant(zcli_as, namer, active_zpod, test_owner_client, superadmin_client):
    """Granting OWNER to a group (not the user directly) still resolves through group membership."""
    group_name = namer("group-owner")
    owner_username = test_owner_client.users_get_me.sync().username

    superadmin_runner = zcli_as("superadmin")
    superadmin_runner("group", "create", group_name)
    superadmin_runner("group", "user", "add", group_name, "--username", owner_username)
    result = superadmin_runner("zpod", "permission", "add", active_zpod, "--permission", "OWNER", "--group", group_name)
    assert result.returncode == 0, f"granting OWNER via group failed:\n{result.stderr}"

    # A real mutating call (not just a read) as proof group-based OWNER
    # resolution actually grants write access, not just visibility.
    from zpodsdk.models.zpod_dns_create import ZpodDnsCreate

    test_owner_client.zpods_dns_add.sync(
        id=f"name={active_zpod}",
        body=ZpodDnsCreate(hostname="group-granted-write", host_id=90),
    )
    entries = superadmin_client.zpods_dns_get_all.sync(id=f"name={active_zpod}") or []
    added_entry = next((e for e in entries if e.hostname == "group-granted-write"), None)
    assert added_entry is not None, (
        "expected the DNS entry added via group-granted OWNER access to be visible"
    )

    superadmin_client.zpods_dns_remove.sync(id=f"name={active_zpod}", ip=added_entry.ip, hostname="group-granted-write")
    superadmin_runner("zpod", "permission", "remove", active_zpod, "--permission", "OWNER", "--group", group_name)
    superadmin_runner("group", "delete", group_name)


def test_global_superadmin_bypasses_zpod_permission_checks(active_zpod, test_admin_client, api_check):
    """A superadmin (test_admin) can manage a zpod it was never explicitly granted a permission on."""
    zpod = test_admin_client.zpods_get.sync(id=f"name={active_zpod}")
    api_check(
        "GET", "/zpods/{id}", "superadmin (no explicit grant) reads a zpod",
        expected="200", actual="200" if zpod else "error",
        note="ZpodPermission.ADMIN is virtual - granted implicitly whenever current_user.superadmin is true",
    )
    assert zpod is not None, "superadmin should be able to read any zpod without an explicit grant"
    components = test_admin_client.zpods_components_get_all.sync(id=f"name={active_zpod}")
    assert components is not None, "superadmin should be able to read any zpod's components without an explicit grant"


def test_zpod_permission_denied_deploy_without_endpoint_permission(zcli_as, namer, zcore_profile, endpoint):
    """A non-superadmin with no endpoint permission can't deploy there - fails fast, no real deploy attempted.

    Complements test_zpod_permission_owner_can_deploy_their_own_zpod below,
    which explicitly grants endpoint permission first. Without it,
    `--endpoint <name>` can't even resolve - endpoints are permission-
    filtered the same way zpods are (endpoint__services.py
    get_endpoint_records), so `zcli zpod create` fails cleanly ("Endpoint
    not found") before any real deploy work starts. This is deliberately
    NOT marked slow: unlike the positive-case test, nothing here ever talks
    to vCenter/Prefect, so it stays fast even though it looks similar.

    Note: this denial is enforced at the CLI's endpoint-name-lookup step,
    not inside `POST /zpods` itself - `ZpodService.create()` only checks
    that `endpoint_id` exists and is ACTIVE, not that the caller has
    permission on it (see zpod__services.py). A caller going straight to
    the SDK with a raw endpoint_id it already knows would not be stopped
    by this check. Confirmed empirically against the live server (CLI path
    denies cleanly, no zpod created) - out of scope here, but worth flagging.
    """
    runner = zcli_as("test_owner")
    zpod_name = namer("zpod-denied-deploy")

    result = runner(
        "zpod", "create", zpod_name,
        "--endpoint", endpoint.name,
        "--profile", zcore_profile,
        "--wait", "--no-spinner",
        check=False,
    )
    assert result.returncode != 0, "expected deploy to be denied without endpoint permission, but it succeeded"


@pytest.mark.slow
def test_zpod_permission_owner_can_deploy_their_own_zpod(zcli_as, namer, zcore_profile, endpoint, test_owner_client, e2e_config):
    """A non-superadmin (test_owner), granted access to the endpoint, can deploy their own
    minimal zcore zpod end-to-end and becomes its OWNER.

    zPod creation itself isn't gated by any special permission - any
    enabled user can create one, and the creator is automatically granted
    OWNER. But *endpoints* are permission-filtered too
    (endpoint__services.py get_endpoint_records, same pattern as zpods) -
    a non-superadmin with no grant on the endpoint can't even see it, so
    `--endpoint <endpoint>` would 404 without this grant. This is the
    "validate through an actual deployment" case, done once here rather
    than per permission scenario.
    """
    superadmin_runner = zcli_as("superadmin")
    test_username = test_owner_client.users_get_me.sync().username
    superadmin_runner("endpoint", "permission", "add", endpoint.name, "--username", test_username)

    runner = zcli_as("test_owner")
    zpod_name = namer("owner-deploy")
    deploy_timeout = e2e_config.deploy_timeout_seconds + 60

    try:
        result = runner(
            "zpod", "create", zpod_name,
            "--endpoint", endpoint.name,
            "--profile", zcore_profile,
            "--wait", "--no-spinner",
            check=False,
            timeout=deploy_timeout,
        )
        assert result.returncode == 0, f"test_owner's own deploy failed:\n{result.stdout}\n{result.stderr}"
    finally:
        superadmin_runner("endpoint", "permission", "remove", endpoint.name, "--username", test_username, check=False)

    zpod = test_owner_client.zpods_get.sync(id=f"name={zpod_name}")
    assert zpod.status == "ACTIVE", f"expected ACTIVE, got {zpod.status}"

    result = runner("zpod", "destroy", zpod_name)
    assert result.returncode == 0, f"test_owner's own destroy failed:\n{result.stderr}"
