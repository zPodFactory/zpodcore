import json
import subprocess
import time
from pathlib import Path

from jinja2 import Template

from zpodcommon import models as M
from zpodcommon.lib.network import INSTANCE_PUBLIC_SUB_NETWORKS_PREFIXLEN, get_mgmt_ip


def get_json_from_file(filename: str):
    if not Path(filename).is_file():
        raise ValueError(f"The provided {filename} does not exist")
    with open(filename, "r") as f:
        return json.load(f)


def ovf_deployer(instance_component: M.InstanceComponent):
    c = instance_component.component
    i = instance_component.instance

    # Open Component JSON
    f = open(c.jsonfile)

    # Load govc deploy spec
    govc_spec = json.load(f)["component_deploy_govc_spec"]

    # Fetch component IP address from instance
    component_ipaddress = get_mgmt_ip(i, c.component_name)

    # Fetch component default gw from instance
    component_gateway = get_mgmt_ip(i, "gw")

    t = Template(json.dumps(govc_spec))
    govc_spec_render = t.render(
        zpod_hostname=c.component_name,
        zpod_ipaddress=component_ipaddress,
        zpod_netprefix=INSTANCE_PUBLIC_SUB_NETWORKS_PREFIXLEN,
        zpod_gateway=component_gateway,
        zpod_dns="10.96.42.11",  # TBD
        zpod_domain=i.domain,
        zpod_password=i.password,
        zpod_sshkey="",
        zpod_portgroup=f"Segment-zPod-{i.name}",
    )

    print("govc ovf property options generated file")
    print(govc_spec_render)

    options_filename = f"/tmp/{i.name}-{c.component_uid}.json"
    with open(options_filename, "w") as f:
        f.write(govc_spec_render)

    hostname = i.endpoint.endpoints["compute"]["hostname"]
    username = i.endpoint.endpoints["compute"]["username"]
    password = i.endpoint.endpoints["compute"]["password"]

    url = f"https://{username}:{password}@{hostname}/sdk"

    cmd = (
        "govc import.ova"
        " -k"
        f" -name={c.component_name}.{i.domain}"
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
            return RuntimeError(message=f"govc error: {h.stderr}")

    except subprocess.CalledProcessError as e:
        print(e.output)
