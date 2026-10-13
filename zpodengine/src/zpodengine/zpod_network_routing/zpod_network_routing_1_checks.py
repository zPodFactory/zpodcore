from sqlmodel import select

from zpodcommon import models as M
from zpodcommon.lib.zboxapi import HTTPStatusError, ZboxApiClient


def fetch_zpod_network_rows(session) -> list[dict]:
    """Every zPod network row with its zPod's name and status (the check drops
    deleted zPods itself, so the inventory shows what was considered)."""
    rows = session.exec(
        select(M.ZpodNetwork, M.Zpod).join(M.Zpod, M.Zpod.id == M.ZpodNetwork.zpod_id)
    ).all()
    return [
        {
            "zpod": zpod.name,
            "zpod_status": zpod.status,
            "network": network.name,
            "network_id": network.id,
            "cidr": str(network.cidr),
        }
        for network, zpod in rows
    ]


def check_zcore_vlan(zpod: M.Zpod, vlan_id: int) -> dict:
    """The VLAN interface exists on zcore and is up."""
    print(f"[zcore_vlan] GET /vlan/{vlan_id} on zcore.{zpod.domain}")
    with ZboxApiClient.by_zpod(zpod) as zb:
        try:
            view = zb.get(url=f"/vlan/{vlan_id}").safejson()
        except HTTPStatusError as e:
            raise ValueError(
                f"FAIL: VLAN {vlan_id} is not configured on zcore of zPod {zpod.name} "
                f"(zboxapi answered HTTP {e.response.status_code})"
            ) from e
    status = view.get("status")
    detail = (
        "ok"
        if status == "up"
        else f"FAIL: VLAN {vlan_id} interface {view.get('interface')} on zcore is {status!r}, not up"
    )
    print(f"[zcore_vlan] {view}")
    print(f"[zcore_vlan] {detail}")
    if status != "up":
        raise ValueError(detail)
    return {
        "ok": True,
        "count": 1,
        "detail": detail,
        "inventory": [
            f"vlan {vlan_id} interface={view.get('interface')} status={status}"
        ],
    }
