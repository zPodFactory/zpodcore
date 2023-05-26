from zpodcommon import models as M
from zpodcommon.lib.vmware import vCenter


def zpod_endpoint_check(endpoint: M.Endpoint):
    print(f"Checking Endpoint: {endpoint.name}...")

    try:
        vc = vCenter.auth_by_endpoint(endpoint)
    except Exception as e:
        return f"Connection Error to endpoint ({e})"

    with vc:
        portgroups = vc.get_portgroups()
        for pg in portgroups:
            print(pg.name)

    return True


def update_dictionary(target_dict, update_dict):
    for key, value in update_dict.items():
        if isinstance(value, dict):
            # If value is a dictionary, recursively call update_dict with the nested
            # dictionaries
            if key in target_dict and isinstance(target_dict[key], dict):
                update_dictionary(target_dict[key], value)
            else:
                target_dict[key] = value
        else:
            # If value is not a dictionary, update the key with the new value
            target_dict[key] = value
