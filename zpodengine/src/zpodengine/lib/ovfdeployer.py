import json

from jinja2 import Template

from zpodcommon import models as M
from zpodengine import settings
from zpodengine.lib.commands import cmd_execute
from zpodengine.lib.dbutils import DBUtils
from zpodengine.lib.network import INSTANCE_PUBLIC_SUB_NETWORKS_PREFIXLEN, MgmtIp


def ovf_deployer(instance_component: M.InstanceComponent):
    component = instance_component.component
    instance = instance_component.instance

    # Open Component JSON file
    f = open(component.jsonfile)

    # Load component JSON
    cjson = json.load(f)

    # Load govc deploy spec
    govc_spec = cjson["component_deploy_govc_spec"]

    # Fetch component default gw and netmask from instance
    gw = MgmtIp.instance(instance, "gw")
    zpod_netmask = gw.netmask
    component_gateway = gw.ip

    zpodfactory_host = DBUtils.get_setting_value("zpodfactory_host")
    zpodfactory_ssh_key = DBUtils.get_setting_value("zpodfactory_ssh_key")

    if component.component_name in ["zbox", "vyos"]:
        # zpodfactory is the main DNS server for every instance and links to zbox/vyos
        # as DNS servers for their respective subdomain.
        #
        # For those 2 components, the DNS Server must be the zpodfactory_host.
        zpod_dns = zpodfactory_host
    else:
        # all other components rely on zbox/vyos as their DNS server.
        zpod_dns = MgmtIp.instance(instance, "zbox").ip

    print(f"Component Nested: {cjson['component_isnested']}")

    if cjson["component_isnested"] is False:
        print(f"[L1] Deployment for {component.component_name}")
        # This means we deploy on the physical endpoint vSphere env
        epc = instance.endpoint.endpoints["compute"]
        hostname = epc["hostname"]
        username = epc["username"]
        password = epc["password"]
        datastore = epc["storage_datastore"]
        # FIXME: we might want this in a zcli setting key/value ?
        # if set, then set prefix, else default to normal one.
        site_id = settings.SITE_ID
        resource_pool = f"{site_id}-{instance.name}"
        zpod_portgroup = f"{site_id}-{instance.name}-segment"
        vm_name = instance_component.fqdn

    else:
        print(f"[L2] Deployment for {component.component_name}")
        # This means we deploy the component as a nested L2 VM from the instance
        # vSphere env
        hostname = f"vcsa.{instance.domain}"
        username = f"administrator@{instance.domain}"
        password = instance.password

        # For now this is hardcoded unless anything changes
        resource_pool = "Cluster/Resources"
        # For now this is hardcoded unless anything changes
        # (maybe vSAN OSA/ESA support in the future instead of NFS-01)
        datastore = "NFS-01"
        zpod_portgroup = "VM Network"
        vm_name = instance_component.hostname

    # Add zbox as this is a mandatory infrastructure component
    zpod_zbox_ipaddress = MgmtIp.instance(instance, "zbox").ip
    url = f"https://{username}:{password}@{hostname}/sdk"
    print(f"Deploying to [https://{username}:XXXXXXXX@{hostname}/sdk]...")

    t = Template(json.dumps(govc_spec))
    govc_spec_render = t.render(
        zpod_hostname=instance_component.hostname,
        zpod_ipaddress=instance_component.ip,
        zpod_netmask=zpod_netmask,
        zpod_netprefix=INSTANCE_PUBLIC_SUB_NETWORKS_PREFIXLEN,
        zpod_gateway=component_gateway,
        zpod_dns=zpod_dns,
        zpod_nfs=zpod_zbox_ipaddress,
        zpod_ntp=zpodfactory_host,
        zpod_domain=instance.domain,
        zpod_password=instance.password,
        zpod_sshkey=zpodfactory_ssh_key,
        zpod_portgroup=zpod_portgroup,
    )

    print("govc ovf property options generated file")
    print(govc_spec_render)

    options_filename = f"/tmp/{instance_component.fqdn}.json"
    with open(options_filename, "w") as f:
        f.write(govc_spec_render)

    cmd = (
        "govc import.ova"
        " -k"
        f" -name={vm_name}"
        f" -u='{url}'"
        f" -pool={resource_pool}"
        f" -ds={datastore}"
        " -json=true"  # this avoids prefect crashing on the live output
        f" -options={options_filename}"
        f" /products/{component.component_name}/{component.component_version}/{component.filename}"  # noqa: E501 B950
    )
    print("govc deploy command")
    print(cmd)

    cmd_execute(cmd)
