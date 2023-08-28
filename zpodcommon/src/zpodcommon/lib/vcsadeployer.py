import json
import os

from jinja2 import Template
from rich import print as pprint

from zpodcommon import models as M
from zpodcommon.lib.commands import cmd_execute
from zpodcommon.lib.dbutils import DBUtils
from zpodcommon.lib.network import INSTANCE_PUBLIC_SUB_NETWORKS_PREFIXLEN, MgmtIp


def vcsa_extract_iso(component: M.Component):
    # Customer Connect provides an ISO for the vcsa component.
    # It cannot be used directly so some preparation is required.
    # First step is to extract the content of ISO and prepare the structure
    # for automation tools.

    path_component = (
        f"/products/{component.component_name}/{component.component_version}"
    )
    if os.path.isdir(f"{path_component}/extracted_iso"):
        print(f"Directory: {path_component}/extracted_iso")
        return

    cmd = (
        "7z"
        " x"
        f" {path_component}/{component.filename}"
        f" -bd"  # do not show live progress
        f" -o{path_component}/extracted_iso"
    )

    return cmd_execute(cmd)


def vcsa_fix_permissions(component: M.Component):
    path_component = (
        f"/products/{component.component_name}/{component.component_version}"
    )
    path_ovftool = "extracted_iso/vcsa/ovftool/lin64/ovftool*"

    # Set execute permissions on ovftool
    path_vcsa_cli = "extracted_iso/vcsa-cli-installer/lin64/vcsa-deploy*"
    cmd_permissions_ovftool = f"chmod +x {path_component}/{path_ovftool}"
    cmd_execute(cmd_permissions_ovftool)

    # Set execute permissions on vcsa cli installer
    cmd_permissions_vcsa_cli = f"chmod +x {path_component}/{path_vcsa_cli}"
    cmd_execute(cmd_permissions_vcsa_cli)


def vcsa_deployer(instance_component: M.InstanceComponent):
    component = instance_component.component
    instance = instance_component.instance

    print("Deploying vCenter Server")

    # Open Component JSON file
    f = open(component.jsonfile)

    # Load component JSON
    cjson = json.load(f)

    # Load vcsa deploy spec
    vcsa_spec = cjson["component_deploy_vcsa_spec"]

    # Fetch component IP address from instance
    component_ipaddress = MgmtIp.instance_component(instance_component).ip

    zpod_netmask = MgmtIp.instance(instance, "gw").netmask

    # Fetch component default gw from instance
    component_gateway = MgmtIp.instance(instance, "gw").ip

    zpodfactory_host = DBUtils.get_setting_value("zpodfactory_host")
    zpodfactory_ssh_key = DBUtils.get_setting_value("zpodfactory_ssh_key")

    # Specific setting for vcsa, deployed on first mandatory esxi11
    zpod_hostname = "esxi11"

    zpod_dns = zpodfactory_host

    print(f"[L2] Deployment for {component.component_name}")

    # For now this is hardcoded unless anything changes
    # (maybe vSAN OSA/ESA support in the future instead of NFS-01)
    datastore = "NFS-01"
    zpod_portgroup = "VM Network"

    t = Template(json.dumps(vcsa_spec))
    vcsa_spec_render = t.render(
        zpod_hostname=zpod_hostname,
        zpod_ipaddress=component_ipaddress,
        zpod_netmask=zpod_netmask,
        zpod_netprefix=INSTANCE_PUBLIC_SUB_NETWORKS_PREFIXLEN,
        zpod_gateway=component_gateway,
        zpod_dns=zpod_dns,
        zpod_ntp=zpodfactory_host,
        zpod_domain=instance.domain,
        zpod_password=instance.password,
        zpod_datastore=datastore,
        zpod_sshkey=zpodfactory_ssh_key,
        zpod_portgroup=zpod_portgroup,
    )

    print("vcsa spec options generated file")
    pprint(vcsa_spec_render)

    vm_name = f"vcsa.{instance.domain}"

    options_filename = f"/tmp/{vm_name}.json"
    with open(options_filename, "w") as f:
        f.write(vcsa_spec_render)

    path_component = (
        f"/products/{component.component_name}"
        f"/{component.component_version}/extracted_iso"
    )
    path_installer = f"{path_component}/vcsa-cli-installer/lin64/vcsa-deploy"

    cmd = (
        f"{path_installer} install"
        " --no-ssl-certificate-verification"
        " --accept-eula"
        " --acknowledge-ceip"
        f" {options_filename}"
    )
    print("vcsa deploy command")
    print(cmd)

    cmd_execute(cmd)
