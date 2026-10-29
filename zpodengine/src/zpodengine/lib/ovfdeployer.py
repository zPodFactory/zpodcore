import json
import urllib.parse

from zpodcommon import models as M
from zpodcommon.lib.component_network import (
    clean_network,
    resolve_component_network,
    select_portgroup,
)
from zpodcommon.lib.component_placement import component_isnested
from zpodcommon.lib.dbutils import DBUtils
from zpodcommon.lib.network_utils import MgmtIp
from zpodcommon.lib.vmware import vCenter
from zpodengine import settings
from zpodengine.lib.commands import cmd_execute
from zpodengine.lib.deploy_spec import render_deploy_spec, render_extra_config
from zpodengine.lib.network import ZPOD_PUBLIC_SUB_NETWORKS_PREFIXLEN


def ovf_deployer(
    zpod_component: M.ZpodComponent,
    nested: bool | None = None,
    network: dict | None = None,
    vlan_id: int | None = None,
):
    component = zpod_component.component
    zpod = zpod_component.zpod

    # Load govc deploy spec
    govc_spec = component.component_json["component_deploy_govc_spec"]

    # Fetch component default gw and netmask from zpod
    gw = MgmtIp.zpod(zpod, "gw")
    zpod_netmask = gw.netmask
    component_gateway = gw.ip

    zpodfactory_host = DBUtils.get_setting_value("zpodfactory_host")
    zpodfactory_ssh_key = DBUtils.get_setting_value("zpodfactory_ssh_key")

    if component.component_name in ("zcore", "vyos"):
        # zpodfactory is the main DNS server for every zpod and links to zcore/vyos
        # as DNS servers for their respective subdomain.
        #
        # For those 2 components, the DNS Server must be the zpodfactory_host.
        zpod_dns = zpodfactory_host
    else:
        # all other components rely on zcore/vyos as their DNS server.
        zpod_dns = MgmtIp.zpod(zpod, "zcore").ip

    isnested = component_isnested(component.component_json, nested)
    print(f"Component Nested: {isnested}")

    # Nested components only (the API refuses it otherwise): the network object
    # replaces the address, gateway, DNS and portgroup computed above.
    # vlan_id (any placement, for guests told their VLAN, like ESXi): the address
    # is on the zPod network with that VLAN, and zpod_vlan carries the tag.
    net = None
    if (isnested and clean_network(network)) or vlan_id is not None:
        net = resolve_component_network(
            zpod,
            component.component_name,
            network=network if isnested else None,
            ip=zpod_component.ip,
            vlan_id=vlan_id,
        )
        print(
            f"Component network: {net.ip}/{net.prefixlen} gw {net.gateway} "
            f"dns {net.dns} portgroup {net.portgroup or 'default'} "
            f"vlan {net.vlan_id or 'untagged'}"
        )

    if isnested is False:
        print(f"[L1] Deployment for {component.component_name}")
        # This means we deploy on the physical endpoint vSphere env
        epc = zpod.endpoint.endpoints["compute"]
        hostname = epc["hostname"]
        username = epc["username"]
        password = urllib.parse.quote(epc["password"])
        datacenter = epc["datacenter"]
        datastore = epc["storage_datastore"]
        vds_name = epc.get("vds", "")
        # FIXME: we might want this in a zcli setting key/value ?
        # if set, then set prefix, else default to normal one.
        site_id = settings.SITE_ID
        resource_pool = f"{site_id}-{zpod.name}"
        zpod_portgroup = f"{site_id}-{zpod.name}-segment"
        # In environments where multiple clusters share the same NSX-T
        # overlay transport zone but sit on different VDS's, the zpod
        # segment portgroup gets created on every one of those VDS's under
        # the same name (each with its own identifier). `govc import.ova`
        # then can't tell which of the identically-named portgroups to
        # attach to and fails. Providing the full inventory path
        # (datacenter/network/vds/segment) disambiguates it. If no VDS is
        # configured, there's only one portgroup with that name and govc
        # resolves it fine by bare name. This only applies to govc's own
        # object finder (`govc import.ova -options=...`); pyVmomi lookups
        # elsewhere (vCenter.get_portgroup) match on the bare `name`
        # property and must keep using `zpod_portgroup` as-is.
        if vds_name:
            zpod_portgroup_path = f"/{datacenter}/network/{vds_name}/{zpod_portgroup}"
        else:
            zpod_portgroup_path = zpod_portgroup
        vm_name = zpod_component.fqdn
    else:
        print(f"[L2] Deployment for {component.component_name}")
        # This means we deploy the component as a nested L2 VM from the zpod
        # vSphere env
        hostname = f"vcsa.{zpod.domain}"
        username = f"administrator@{zpod.domain}"
        password = urllib.parse.quote(zpod.password)

        # For now this is hardcoded unless anything changes
        resource_pool = "Cluster/Resources"
        datacenter = "Datacenter"
        # For now this is hardcoded unless anything changes
        # (maybe vSAN OSA/ESA support in the future instead of NFS-01)
        datastore = "NFS-01"
        zpod_portgroup = (net and net.portgroup) or "VM Network"
        # No VDS concept for nested L2 vCenters (standard vSwitch).
        zpod_portgroup_path = zpod_portgroup
        vm_name = zpod_component.hostname
        if net and net.portgroup:
            # Never created: it must already exist in the zPod's vCenter.
            check_nested_portgroup(zpod, net.portgroup)

    # Add the core component (zcore) as a mandatory infrastructure component
    zpod_zcore_ipaddress = MgmtIp.zpod(zpod, "zcore").ip
    url = f"https://{username}:{password}@{hostname}/sdk"
    print(f"Deploying to [https://{username}:XXXXXXXX@{hostname}/sdk]...")

    # FF (Feature Flag) support for esxi hostname = fqdn (William Lam templates)
    zpod_component_hostname = zpod_component.hostname
    if component.component_json[
        "component_name"
    ] == "esxi" and DBUtils.get_setting_value("ff_esxi_hostname_is_fqdn"):
        print(
            f"[ff_esxi_hostname_is_fqdn] Setting hostname to: {zpod_component.fqdn}..."
        )
        zpod_component_hostname = zpod_component.fqdn

    if net:
        zpod_netmask, component_gateway, zpod_dns = net.netmask, net.gateway, net.dns

    variables = {
        "zpod_hostname": zpod_component_hostname,
        "zpod_ipaddress": zpod_component.ip,
        "zpod_netmask": zpod_netmask,
        "zpod_netprefix": net.prefixlen if net else ZPOD_PUBLIC_SUB_NETWORKS_PREFIXLEN,
        "zpod_gateway": component_gateway,
        "zpod_dns": zpod_dns,
        "zpod_nfs": zpod_zcore_ipaddress,
        "zpod_ntp": zpodfactory_host,
        "zpod_domain": zpod.domain,
        "zpod_password": zpod.password,
        "zpod_sshkey": zpodfactory_ssh_key,
        "zpod_portgroup": zpod_portgroup_path,
        # ESXi's guestinfo.vlan: the VLAN its management interface tags.
        "zpod_vlan": str(net.vlan_id) if net and net.vlan_id else "",
    }
    govc_spec_render = render_deploy_spec(govc_spec, **variables)

    # guestinfo.* keys set before the first power-on (component_deploy_extra_config).
    # Rendered first, so a bad value fails the deploy before any VM exists. The VM
    # must come up powered off: the deploy step powers it on afterwards.
    extra_config = render_extra_config(
        component.component_json.get("component_deploy_extra_config"), **variables
    )
    if extra_config:
        govc_spec_render["PowerOn"] = False

    print("govc ovf property options generated file")
    print(json.dumps(govc_spec_render, indent=2))

    # FF (Feature Flag): stage the OVA once into a VM Template and clone it for
    # every subsequent L1 deployment instead of re-uploading it each time.
    # Only L1 components (component_isnested is False) land on the endpoint
    # vCenter. Any failure falls back to the direct OVA import below.
    deployed = False
    if (
        isnested is False
        and DBUtils.get_setting_value("ff_endpoint_ova_staging") == "true"
    ):
        try:
            from zpodengine.lib.ova_staging import deploy_from_template

            deploy_from_template(
                zpod=zpod,
                component=component,
                compute=zpod.endpoint.endpoints["compute"],
                govc_spec=govc_spec,
                real_property_values={
                    pm["Key"]: pm["Value"]
                    for pm in govc_spec_render.get("PropertyMapping", [])
                },
                vm_name=vm_name,
                vapp_pool_name=resource_pool,
                portgroup_name=zpod_portgroup,
                govc_url=url,
            )
            deployed = True
        except Exception as e:
            print(
                "[ff_endpoint_ova_staging] staging/clone failed, falling back to "
                f"direct OVA import: {e}"
            )

    if not deployed:
        govc_import(
            vm_name=vm_name,
            url=url,
            resource_pool=resource_pool,
            datastore=datastore,
            datacenter=datacenter,
            component=component,
            options=govc_spec_render,
            options_filename=f"/tmp/{zpod_component.fqdn}.json",
        )

    if extra_config:
        auth = vCenter.auth_by_zpod if isnested else vCenter.auth_by_zpod_endpoint
        with auth(zpod=zpod) as vc:
            vm = vc.get_vm(name=vm_name)
            if vm is None:
                raise RuntimeError(f"{vm_name} not found to set its extra config")
            # Key names and sizes only: userdata can hold the zPod password.
            for key, value in extra_config.items():
                print(f"Set extraConfig {key} ({len(value)} chars)")
            vc.set_extra_config(vm, extra_config)


def govc_import(
    *,
    vm_name,
    url,
    resource_pool,
    datastore,
    datacenter,
    component,
    options,
    options_filename,
):
    """Import the OVA with govc, the rendered spec as its options file."""
    with open(options_filename, "w") as f:
        json.dump(options, f)

    cmd = (
        "govc import.ova"
        " -k"
        f" -name={vm_name}"
        f" -u='{url}'"
        f" -pool={resource_pool}"
        f" -ds={datastore}"
        " -json=true"  # this avoids prefect crashing on the live output
        " -hidden=true"
        f" -options={options_filename}"
        f" -dc={datacenter}"
        f" /products/{component.component_name}/{component.component_version}/{component.filename}"  # noqa: E501 B950
    )
    print("govc deploy command")
    print(cmd)

    cmd_execute(cmd)


def check_nested_portgroup(zpod: M.Zpod, portgroup: str):
    """Fail before the import unless `portgroup` is exactly one network of the
    zPod's vCenter, present on every host of its cluster when it is a standard
    vSwitch portgroup."""
    with vCenter.auth_by_zpod(zpod=zpod) as vc:
        match = select_portgroup(vc, portgroup, f"vcsa.{zpod.domain}")
    print(f"Portgroup {portgroup!r}: {match['path']} (VLAN {match['vlan']})")
