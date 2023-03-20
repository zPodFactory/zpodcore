from zpodengine.deploy.components import (
    deploy_esxi,
    deploy_nsxt,
    deploy_vcenter,
    deploy_zbox,
)


def flow():
    zbox_future = deploy_zbox.submit()
    vcenter_future = deploy_vcenter.submit(wait_for=zbox_future)
    esxi_futures = [
        deploy_esxi.submit(f"esxi{i}", wait_for=vcenter_future) for i in range(11, 14)
    ]
    deploy_nsxt.submit(wait_for=esxi_futures)
