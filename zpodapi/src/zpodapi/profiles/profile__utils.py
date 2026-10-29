from fastapi import HTTPException, status
from sqlmodel import Session, select

from zpodcommon import models as M
from zpodcommon.enums import ComponentStatus
from zpodcommon.lib.component_network import (
    deploy_network_host_id_error,
    network_static_error,
)
from zpodcommon.lib.component_placement import component_options_error
from zpodcommon.lib.dbutils import DBUtils

# Linux caps the system hostname (sethostname(2), hostnamectl) at 64 chars,
# even when it is a full FQDN. DNS itself allows far more, so an FQDN can be
# perfectly resolvable yet fail to apply as the guest OS hostname at deploy.
MAX_LINUX_HOSTNAME_LENGTH = 64
DEFAULT_FQDN_RESERVED_CHARS = 8


def walk_profile(profile_obj):
    for profile_item in profile_obj:
        if isinstance(profile_item, list):
            yield from profile_item
        else:
            yield profile_item


def validate_profile(session: Session, profile_obj: list):
    # Get all component_uids in profile
    component_uids = {x["component_uid"] for x in walk_profile(profile_obj)}

    # Get the components from db
    db_components = {
        c.component_uid: c
        for c in session.exec(
            select(M.Component).where(M.Component.component_uid.in_(component_uids))
        ).all()
    }
    components = {uid: c.status for uid, c in db_components.items()}

    # Validate
    errors = []
    for component_uid in component_uids:
        # Validate that component_uid is in db
        if component_uid not in components:
            errors.append(f"Invalid component_uid: {component_uid}")
        # Validate that component is active
        elif components.get(component_uid) != ComponentStatus.ACTIVE:
            errors.append(f"Component is not ACTIVE: {component_uid}")

    for item in walk_profile(profile_obj):
        # The deploy networks are laid out the same in every zPod.
        if error := deploy_network_host_id_error(
            item.get("host_id"), item.get("vlan_id"), item.get("network")
        ):
            errors.append(f"{item['component_uid']}: {error}")
        component = db_components.get(item["component_uid"])
        # Only items with deploy options need the component's library JSON.
        if component is None or not any(
            item.get(key) is not None
            for key in ("nested", "network", "vnics", "vlan_id")
        ):
            continue
        # The zPod does not exist yet: its networks are checked at deploy.
        if error := component_options_error(
            component.component_name,
            component.component_json,
            nested=item.get("nested"),
            network=item.get("network"),
            vnics=item.get("vnics"),
            vlan_id=item.get("vlan_id"),
        ) or network_static_error(item.get("network"), item.get("host_id")):
            errors.append(f"{item['component_uid']}: {error}")
        elif item.get("vlan_id") is not None and item.get("host_id") is None:
            errors.append(
                f"{item['component_uid']}: vlan_id needs host_id, the address on it"
            )

    # The mandatory core component (zcore-*) must be the first element.
    first = profile_obj[0] if profile_obj else None
    if not isinstance(first, dict) or not str(
        first.get("component_uid", "")
    ).startswith("zcore-"):
        errors.append(
            "Profile must start with a zcore-* core component as its "
            "first element (legacy zbox profiles must be migrated first)"
        )

    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="\n  ".join(errors),
        )


def compute_zpod_domain(*, zpod_name: str, domain: str) -> str:
    """Mirror zpod_deploy_1_prep.py: an explicit domain wins as-is, otherwise
    it's `<zpod_name>.<zpodfactory_default_domain>`."""
    if domain:
        return domain
    default_domain = DBUtils.get_setting_value("zpodfactory_default_domain") or ""
    return f"{zpod_name}.{default_domain}"


def check_fqdn_length(fqdn: str):
    """Raise 400 if `fqdn` would exceed the Linux hostname limit minus the
    configurable safety margin (`zpodfactory_fqdn_reserved_chars`, default 8)."""
    reserved_chars = int(
        DBUtils.get_setting_value("zpodfactory_fqdn_reserved_chars")
        or DEFAULT_FQDN_RESERVED_CHARS
    )
    max_len = MAX_LINUX_HOSTNAME_LENGTH - reserved_chars
    if len(fqdn) <= max_len:
        return
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            f"zPod FQDN naming is too long: '{fqdn}' is {len(fqdn)} characters, "
            f"which exceeds the {max_len}-character limit "
            f"({MAX_LINUX_HOSTNAME_LENGTH}-character Linux kernel hostname limit "
            f"minus a {reserved_chars}-character safety margin, see the "
            "'zpodfactory_fqdn_reserved_chars' setting). "
            "hostnamectl/sethostname(2) cap the system hostname at "
            f"{MAX_LINUX_HOSTNAME_LENGTH} characters even for a full FQDN: DNS "
            "would accept this name, but the guest OS would fail to set its "
            "hostname during customization. Use a shorter zPod name, a shorter "
            "domain, or a shorter component hostname."
        ),
    )


def validate_fqdn_length(
    session: Session,
    profile_obj: list,
    zpod_name: str,
    domain: str,
):
    """Reject a profile whose longest resulting component FQDN is too long.

    Computes, at request time, the same FQDN a deploy would later build in
    zpod_deploy_1_prep.py (domain) and zpod_component_add_1_prep.py (hostname),
    since nothing is persisted yet when POST /zpods is validated.
    """
    zpod_domain = compute_zpod_domain(zpod_name=zpod_name, domain=domain)

    component_uids = {x["component_uid"] for x in walk_profile(profile_obj)}
    component_names = dict(
        session.exec(
            select(
                M.Component.component_uid,
                M.Component.component_name,
            ).where(
                M.Component.component_uid.in_(component_uids),
            )
        ).fetchall()
    )

    longest_fqdn = ""
    for item in walk_profile(profile_obj):
        hostname = item.get("hostname") or component_names.get(
            item["component_uid"], ""
        )
        fqdn = f"{hostname}.{zpod_domain}"
        if len(fqdn) > len(longest_fqdn):
            longest_fqdn = fqdn

    check_fqdn_length(longest_fqdn)
