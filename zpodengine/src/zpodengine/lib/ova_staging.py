"""OVA staging orchestration for ``ff_endpoint_ova_staging``.

Instead of uploading an OVA from the zPodFactory host to the endpoint vCenter on
every zPod deployment (network/resource intensive), upload it once into a
``components-staging`` folder, switch it into a VM Template, and clone that
template for every subsequent deployment, injecting the per-zPod OVF properties
and portgroup at clone time.

This module is pure orchestration — the govc upload, the atomic DB claim and the
spec rendering. All vCenter/pyVmomi operations live on
``zpodcommon.lib.vmware.vCenter`` (``get_or_create_folder``, ``clone_template``,
``get/set_custom_field``, ``get_network``, ``inventory_path``, ``delete_vm``…).

Only used for L1 components (``component_isnested is False``). The template is
NEVER powered on (powering it on would consume the one-shot OVF customization
and break every later clone). Everything here is best-effort and idempotent: the
caller falls back to a plain ``govc import.ova`` if anything raises.
"""

import json
import time

from jinja2 import Template
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from zpodcommon import models as M
from zpodcommon.lib.vmware import vCenter
from zpodengine.lib import database
from zpodengine.lib.commands import cmd_execute

STAGING_FOLDER = "components-staging"
STATUS_FIELD = "zpodfactory_staging_status"
STATUS_READY = "staged"
LOCK_PREFIX = "_ova_staging_lock_"

# A staging upload can be slow (multi-GB OVA). Waiters poll this long for the
# elected stager to finish before giving up (the caller then falls back to a
# direct import).
POLL_SECONDS = 15
MAX_WAIT_SECONDS = 60 * 60


def deploy_from_template(
    *,
    zpod: M.Zpod,
    component: M.Component,
    compute: dict,
    govc_spec: dict,
    real_property_values: dict,
    vm_name: str,
    vapp_pool_name: str,
    portgroup_name: str,
    govc_url: str,
):
    """Ensure a staged template exists for ``component`` then clone it to
    ``vm_name`` (powered off) with the per-zPod OVF properties and portgroup.

    Raises on any failure so the caller can fall back to a direct OVA import.
    """
    with vCenter.auth_by_zpod_endpoint(zpod=zpod) as vc:
        # Idempotent: nothing to do if this VM is already deployed.
        if vc.get_vm(name=vm_name) is not None:
            print(f"[ova_staging] {vm_name} already exists, skipping clone")
            return

        staging_folder = vc.get_or_create_folder(compute["vmfolder"], STAGING_FOLDER)

        template = ensure_staged_template(
            vc,
            endpoint_id=zpod.endpoint.id,
            component=component,
            staging_folder=staging_folder,
            compute=compute,
            govc_spec=govc_spec,
            govc_url=govc_url,
        )

        print(f"[ova_staging] cloning {component.component_uid} -> {vm_name}")
        vc.clone_template(
            template=template,
            name=vm_name,
            resource_pool_name=vapp_pool_name,
            datastore_name=compute["storage_datastore"],
            folder_name=compute["vmfolder"],
            vapp_properties=real_property_values,
            portgroup_name=portgroup_name,
        )


def ensure_staged_template(
    vc, *, endpoint_id, component, staging_folder, compute, govc_spec, govc_url
):
    """Return the staged VM Template for ``component``, staging it once if
    needed. Concurrency is handled by an atomic DB claim (one elected stager)
    plus a ``staged`` custom attribute that waiters poll; a crashed stager is
    transparently taken over."""
    uid = component.component_uid
    waited = 0
    while True:
        template = vc.get_vm(name=uid, root=staging_folder)
        if template is not None and vc.get_custom_field(template, STATUS_FIELD) == STATUS_READY:
            return template

        if try_claim(endpoint_id, uid):
            # We are the elected stager for this component_uid.
            try:
                template = vc.get_vm(name=uid, root=staging_folder)
                if (
                    template is not None
                    and vc.get_custom_field(template, STATUS_FIELD) == STATUS_READY
                ):
                    return template
                if template is not None:
                    # Partial/stale import from a previous crashed attempt.
                    print(f"[ova_staging] removing stale template {uid}")
                    vc.delete_vm(template)

                print(f"[ova_staging] staging OVA for {uid}")
                stage_ova(
                    vc,
                    component=component,
                    compute=compute,
                    staging_folder=staging_folder,
                    govc_spec=govc_spec,
                    govc_url=govc_url,
                )
                template = vc.get_vm(name=uid, root=staging_folder)
                if template is None:
                    raise RuntimeError(f"template {uid} not found after staging")
                vc.set_custom_field(template, STATUS_FIELD, STATUS_READY)
                print(f"[ova_staging] {uid} staged")
                return template
            finally:
                release_claim(endpoint_id, uid)

        # Another worker holds the claim (e.g. a sibling esxi in the same
        # profile). Wait for it to finish, then re-check / take over if it died.
        if waited >= MAX_WAIT_SECONDS:
            raise TimeoutError(f"timed out waiting for {uid} to be staged")
        print(f"[ova_staging] {uid} staging in progress, waiting...")
        time.sleep(POLL_SECONDS)
        waited += POLL_SECONDS


def stage_ova(vc, *, component, compute, staging_folder, govc_spec, govc_url):
    """Upload the OVA once into ``components-staging`` as a VM Template.

    Rendered with neutral placeholder values (the template never boots and every
    property is overridden per-clone) and forced to PowerOn=False so the
    one-shot OVF customization is preserved for the clones.
    """
    network = vc.get_network()
    if network is None:
        raise RuntimeError("no network found on endpoint for staging import")
    options = build_staging_options(govc_spec, network.name)
    options_filename = f"/tmp/{component.component_uid}.staging.json"
    with open(options_filename, "w") as f:
        f.write(json.dumps(options))

    # govc resolves a relative -folder from the datacenter root, so pass the
    # absolute inventory path (/<dc>/vm/<vmfolder>/components-staging).
    folder_path = vc.inventory_path(staging_folder)
    cmd = (
        "govc import.ova"
        " -k"
        f" -name={component.component_uid}"
        f" -u='{govc_url}'"
        f" -pool={compute['resource_pool']}/Resources"
        f" -ds={compute['storage_datastore']}"
        f" -folder='{folder_path}'"
        " -json=true"
        " -hidden=true"
        f" -options={options_filename}"
        f" -dc={compute['datacenter']}"
        f" /products/{component.component_name}/{component.component_version}/{component.filename}"  # noqa: E501 B950
    )
    print(f"[ova_staging] {cmd}")
    cmd_execute(cmd)


def build_staging_options(govc_spec: dict, staging_network: str) -> dict:
    """Render the govc spec with neutral values and force template-safe flags."""
    neutral = {
        "zpod_hostname": "staging",
        "zpod_ipaddress": "",
        "zpod_netmask": "",
        "zpod_netprefix": "",
        "zpod_gateway": "",
        "zpod_dns": "",
        "zpod_nfs": "",
        "zpod_ntp": "",
        "zpod_domain": "",
        "zpod_password": "",
        "zpod_sshkey": "",
        "zpod_portgroup": staging_network,
    }
    options = json.loads(Template(json.dumps(govc_spec)).render(**neutral))
    options["PowerOn"] = False
    options["MarkAsTemplate"] = True
    options["InjectOvfEnv"] = False
    options["WaitForIP"] = False
    return options


# --------------------------------------------------------------------------- #
# Atomic claim (Setting.name is unique -> INSERT is the lock)
# --------------------------------------------------------------------------- #
def lock_name(endpoint_id, uid):
    return f"{LOCK_PREFIX}{endpoint_id}_{uid}"


def try_claim(endpoint_id, uid) -> bool:
    name = lock_name(endpoint_id, uid)
    with database.get_session_ctx() as session:
        session.add(
            M.Setting(name=name, description="ova staging in-progress lock", value="1")
        )
        try:
            session.commit()
            return True
        except IntegrityError:
            session.rollback()
            return False


def release_claim(endpoint_id, uid):
    name = lock_name(endpoint_id, uid)
    with database.get_session_ctx() as session:
        row = session.exec(select(M.Setting).where(M.Setting.name == name)).one_or_none()
        if row is not None:
            session.delete(row)
            session.commit()
