import json
import subprocess
from pathlib import Path

from jinja2 import Template

from zpodcommon import models as M
from zpodcommon.lib.network import (
    INSTANCE_PUBLIC_SUB_NETWORKS_PREFIXLEN,
    get_instance_component_mgmt_ip,
    get_instance_mgmt_ip,
)


def get_json_from_file(filename: str):
    if not Path(filename).is_file():
        raise ValueError(f"The provided {filename} does not exist")
    with open(filename, "r") as f:
        return json.load(f)


def ovf_deployer(instance_component: M.InstanceComponent):
    c = instance_component.component
    i = instance_component.instance

    # Fetch component default gw from instance
    zpod_gateway = get_instance_mgmt_ip(i, "gw")

    if "hostname" in instance_component.data:
        zpod_hostname = instance_component.data["hostname"]
    elif "last_octet" in instance_component.data:
        zpod_hostname = f"{c.component_name}{instance_component.data['last_octet']}"
    else:
        zpod_hostname = c.component_name

    # Open Component JSON
    f = open(c.jsonfile)

    # Load govc deploy spec
    govc_spec = json.load(f)["component_deploy_govc_spec"]

    t = Template(json.dumps(govc_spec))
    govc_spec_render = t.render(
        zpod_hostname=zpod_hostname,
        zpod_ipaddress=get_instance_component_mgmt_ip(instance_component),
        zpod_netprefix=INSTANCE_PUBLIC_SUB_NETWORKS_PREFIXLEN,
        zpod_gateway=zpod_gateway,
        zpod_dns="10.96.42.11",  # TBD
        zpod_domain=i.domain,
        zpod_password=i.password,
        zpod_sshkey="",
        zpod_portgroup=f"Segment-zPod-{i.name}",
    )

    print("govc ovf property options generated file")
    print(govc_spec_render)

    options_filename = f"/tmp/{i.name}-{c.component_uid}-{instance_component.id}.json"
    with open(options_filename, "w") as f:
        f.write(govc_spec_render)

    hostname = i.endpoint.endpoints["compute"]["hostname"]
    username = i.endpoint.endpoints["compute"]["username"]
    password = i.endpoint.endpoints["compute"]["password"]

    url = f"https://{username}:{password}@{hostname}/sdk"

    cmd = (
        "govc import.ova"
        " -k"
        f" -name={zpod_hostname}.{i.domain}"
        f" -u='{url}'"
        f" -pool=zPod-{i.name}"
        " -ds=NFS-01"
        " -json=true"
        f" -options={options_filename}"
        f" /products/{c.component_name}/{c.component_version}/{c.filename}"
    )
    print("govc deploy command")
    print(cmd)

    try:
        h = subprocess.run(
            args=cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            check=False,
        )
        print(h)
        if h.returncode != 0:
            print(h.stderr)
            raise RuntimeError(message=f"govc error: {h.stderr}")

    except subprocess.CalledProcessError as e:
        print(e.output)
